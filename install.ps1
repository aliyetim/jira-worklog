# Jira Worklog setup for Windows. Paste into PowerShell:
#   irm https://raw.githubusercontent.com/aliyetim/jira-worklog/main/install.ps1 | iex
# Downloads the app (~100 KB) and a portable Python (~47 MB) into %LOCALAPPDATA%\jira-worklog and adds
# Start menu and desktop shortcuts. Needs neither Git nor an installed Python, and no administrator rights.
# Running it again is harmless (it updates the app; settings and a saved token are kept).
# Environment: JIRA_WORKLOG_DIR (install folder), JIRA_WORKLOG_NO_SHORTCUTS=1, JIRA_WORKLOG_NO_LAUNCH=1.
#
# Rules for this file:
# - ASCII only: Windows PowerShell 5.1 reads files without a BOM as ANSI.
# - Must work in Constrained Language Mode (company AppLocker/WDAC policies): no .NET type calls, no COM,
#   no Add-Type. Only cmdlets and Windows' own tools (tar.exe, robocopy, certutil). Shortcuts are made by Python.
# - Everything runs inside a function so that "irm | iex" never closes the user's window on errors.

function Install-JiraWorklog {
    $ErrorActionPreference = 'Stop'
    $ProgressPreference = 'SilentlyContinue'  # Invoke-WebRequest is very slow with the progress bar

    $Repo = 'aliyetim/jira-worklog'
    # Portable Python (python-build-standalone, an official CPython build). The version is pinned and the
    # download is checked against these SHA-256 hashes (from the release's SHA256SUMS file).
    $PyRelease = '20261003'
    $PyVersion = '3.12.15'
    $PySha256 = @{
        'x86_64'  = '4b6f0beebbb695a0f3ea237b8c3eaa5bd424f47a7bc25b2fbe3a43390c770f08'
        'aarch64' = '2de96a340fecdabe215094345ed3aea1b473e858bd098360f2253299e18f24d2'
    }
    $ComtypesVersion = '1.4.17'  # used by windows_launcher.py to create the shortcuts

    $Dir = if ($env:JIRA_WORKLOG_DIR) { $env:JIRA_WORKLOG_DIR } else { Join-Path $env:LOCALAPPDATA 'jira-worklog' }
    $Tmp = Join-Path $env:TEMP ('jira-worklog-' + (Get-Random))
    $Tar = Join-Path $env:SystemRoot 'System32\tar.exe'  # built into Windows 10 1803+; not Git's tar

    function Get-Download([string]$Uri, [string]$OutFile, [string]$What) {
        try {
            Invoke-WebRequest -UseBasicParsing -Uri $Uri -OutFile $OutFile
        } catch {
            throw "Could not download $What. Check your internet/VPN connection and try again. ($($_.Exception.Message))"
        }
    }

    function Get-Sha256([string]$Path) {
        try {
            return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash.ToLowerInvariant()
        } catch {
            # certutil prints the hash on the second line (older versions separate the bytes with spaces)
            $out = & certutil.exe -hashfile $Path SHA256
            return ($out[1] -replace '\s', '').ToLowerInvariant()
        }
    }

    function Expand-Tar([string]$Archive, [string]$Destination) {
        New-Item -ItemType Directory -Force -Path $Destination | Out-Null
        & $Tar -xf $Archive -C $Destination --strip-components=1
        if ($LASTEXITCODE -ne 0) { throw "Could not unpack $Archive." }
    }

    try {
        New-Item -ItemType Directory -Force -Path $Dir, $Tmp | Out-Null
        $Dir = (Resolve-Path $Dir).Path

        # A running copy keeps its files locked; close it first.
        Get-Process pythonw, python -ErrorAction SilentlyContinue |
            Where-Object { $_.Path -like "$Dir\*" } |
            ForEach-Object { Write-Host 'Closing the running Jira Worklog app...'; Stop-Process -Id $_.Id -Force }

        # 1) App files. windows_launcher.py checks for updates with the archive's ETag. PowerShell gets a different
        #    (compressed, weak) ETag than Python's urllib, so we store "pending": the first launch fetches the
        #    archive once (~100 KB) and saves the ETag it sees; later launches get 304 and download nothing.
        if (-not (Test-Path (Join-Path $Dir '.git'))) {
            Write-Host "`nDownloading the app..."
            $zip = Join-Path $Tmp 'app.zip'
            Get-Download "https://codeload.github.com/$Repo/zip/refs/heads/main" $zip 'the app'
            $appTmp = Join-Path $Tmp 'app'
            Expand-Tar $zip $appTmp
            if (-not (Test-Path (Join-Path $appTmp 'worklog_web.py'))) { throw 'The downloaded app archive is damaged. Try again.' }
            & robocopy $appTmp $Dir /E /NFL /NDL /NJH /NJS /NP | Out-Null
            if ($LASTEXITCODE -ge 8) { throw "Could not copy the app files into $Dir." }
            Set-Content -Path (Join-Path $Dir '.version') -Value 'pending' -NoNewline -Encoding ASCII
        }

        # 2) Portable Python in .python\ (only when missing or the pinned version changed).
        $arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64' -or $env:PROCESSOR_ARCHITEW6432 -eq 'ARM64') { 'aarch64' } else { 'x86_64' }
        $pin = "$PyVersion+$PyRelease-$arch"
        $pyDir = Join-Path $Dir '.python'
        $pinFile = Join-Path $pyDir '.pin'
        $venvDir = Join-Path $Dir '.venv'
        $havePy = (Test-Path (Join-Path $pyDir 'python.exe')) -and (Test-Path $pinFile) -and ((Get-Content $pinFile -Raw).Trim() -eq $pin)
        if (-not $havePy) {
            Write-Host "`nDownloading Python $PyVersion (about 47 MB)..."
            $name = "cpython-$PyVersion%2B$PyRelease-$arch-pc-windows-msvc-install_only.tar.gz"
            $pyTar = Join-Path $Tmp 'python.tar.gz'
            Get-Download "https://github.com/astral-sh/python-build-standalone/releases/download/$PyRelease/$name" $pyTar 'Python'
            if ((Get-Sha256 $pyTar) -ne $PySha256[$arch]) {
                throw 'The downloaded Python failed its integrity check, so setup was stopped. Try again later.'
            }
            foreach ($old in @($pyDir, $venvDir)) {  # the environment is tied to the old Python; rebuild it
                if (Test-Path $old) { Remove-Item -Recurse -Force $old }
            }
            Expand-Tar $pyTar $pyDir
            Set-Content -Path $pinFile -Value $pin -NoNewline -Encoding ASCII
        }

        # 3) Virtual environment and dependencies
        Write-Host "`nInstalling dependencies (this may take a minute)..."
        $venvPy = Join-Path $venvDir 'Scripts\python.exe'
        if (-not (Test-Path $venvPy)) {
            & (Join-Path $pyDir 'python.exe') -m venv $venvDir
            if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
        }
        $req = Join-Path $Dir 'requirements.txt'
        & $venvPy -m pip install -q --disable-pip-version-check -r $req "comtypes==$ComtypesVersion"
        if ($LASTEXITCODE -ne 0) { throw 'Could not install the dependencies. Check your internet/VPN connection and try again.' }
        Set-Content -Path (Join-Path $venvDir '.req-sha256') -Value (Get-Sha256 $req) -NoNewline -Encoding ASCII

        # 4) Start menu and desktop shortcuts (pythonw.exe runs the launcher without a console window).
        $launcher = Join-Path $Dir 'windows_launcher.py'
        if ($env:JIRA_WORKLOG_NO_SHORTCUTS -ne '1') {
            & $venvPy $launcher --install-shortcuts
            if ($LASTEXITCODE -ne 0) { throw 'Could not create the shortcuts.' }
        }

        Write-Host "`nSetup complete." -ForegroundColor Green
        Write-Host "Installed in: $Dir"
        Write-Host 'Open "Jira Worklog" from the Start menu or the desktop shortcut.'
        if ($env:JIRA_WORKLOG_NO_LAUNCH -ne '1') {
            Write-Host 'Opening it now...'
            Start-Process -FilePath (Join-Path $venvDir 'Scripts\pythonw.exe') -ArgumentList ('"' + $launcher + '"') -WorkingDirectory $Dir
        }
    } catch {
        $msg = $_.Exception.Message
        Write-Host "`nSetup failed: $msg" -ForegroundColor Red
        if ($msg -match 'group policy|Application Control|AppLocker|blocked') {
            Write-Host ("Your computer's security policy does not allow programs to run from $Dir. " +
                        'Please ask IT to allow this folder (or to install Jira Worklog for you).') -ForegroundColor Yellow
        }
        Write-Host "(PowerShell language mode: $($ExecutionContext.SessionState.LanguageMode))"
    } finally {
        if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue }
    }
}

Install-JiraWorklog
