# Jira Worklog setup for Windows. Paste into PowerShell:
#   irm https://raw.githubusercontent.com/aliyetim/jira-worklog/main/install.ps1 | iex
# Downloads the app (~100 KB) into %LOCALAPPDATA%\jira-worklog and adds Start menu and desktop shortcuts.
# Python: an installed Python 3.9+ is used when there is one (e.g. from the company software portal); otherwise a
# portable Python (~47 MB) is downloaded. Needs no Git and no administrator rights.
# Dependencies go to .deps\ as plain Python files (pip --target, no virtual environment), so no program is ever run
# from the install folder: application control policies (AppLocker/WDAC) that block .exe files in user folders
# still allow the app when Python itself is installed in an allowed place.
# Running it again is harmless (it updates the app; settings and a saved token are kept).
# Environment: JIRA_WORKLOG_DIR (install folder), JIRA_WORKLOG_PYTHON (python.exe to use),
#              JIRA_WORKLOG_NO_SHORTCUTS=1, JIRA_WORKLOG_NO_LAUNCH=1.
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

    # Returns the path of an installed Python 3.9+ (sys.executable), or $null.
    function Find-InstalledPython {
        $ErrorActionPreference = 'Continue'  # PowerShell 5.1 would turn redirected stderr into a terminating error
        $probe = "import sys; print('ok|' + sys.executable if sys.version_info >= (3, 9) else 'too-old')"
        $candidates = @()
        if ($env:JIRA_WORKLOG_PYTHON) { $candidates += $env:JIRA_WORKLOG_PYTHON }
        $candidates += @(Get-Command py.exe, python.exe -All -ErrorAction SilentlyContinue | ForEach-Object { $_.Source })
        $candidates += @(Get-ChildItem -Path "$env:ProgramFiles\Python3*\python.exe", "$env:SystemDrive\Python3*\python.exe", "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
        foreach ($candidate in $candidates) {
            try {
                $pyArgs = if ((Split-Path $candidate -Leaf) -eq 'py.exe') { @('-3', '-c', $probe) } else { @('-c', $probe) }
                $out = @(& $candidate @pyArgs 2>$null)
                if ($LASTEXITCODE -eq 0 -and $out.Count -gt 0 -and "$($out[0])" -match '^ok\|(.+)$') { return $Matches[1].Trim() }
            } catch { }  # blocked by policy, Microsoft Store alias without Python, ...
        }
        return $null
    }

    function Expand-Tar([string]$Archive, [string]$Destination) {
        New-Item -ItemType Directory -Force -Path $Destination | Out-Null
        & $Tar -xf $Archive -C $Destination --strip-components=1
        if ($LASTEXITCODE -ne 0) { throw "Could not unpack $Archive." }
    }

    try {
        New-Item -ItemType Directory -Force -Path $Dir, $Tmp | Out-Null
        $Dir = (Resolve-Path $Dir).Path

        # Close a running copy first (its Python may live elsewhere, so match the launcher in the command line).
        Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like "*$Dir\windows_launcher.py*" } |
            ForEach-Object { Write-Host 'Closing the running Jira Worklog app...'; Stop-Process -Id $_.ProcessId -Force }

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

        # 2) Python: an installed one if available, otherwise a portable one in .python\.
        $python = Find-InstalledPython
        if ($python) {
            Write-Host "`nUsing the installed Python: $python"
        } else {
            $arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64' -or $env:PROCESSOR_ARCHITEW6432 -eq 'ARM64') { 'aarch64' } else { 'x86_64' }
            $pin = "$PyVersion+$PyRelease-$arch"
            $pyDir = Join-Path $Dir '.python'
            $pinFile = Join-Path $pyDir '.pin'
            $havePy = (Test-Path (Join-Path $pyDir 'python.exe')) -and (Test-Path $pinFile) -and ((Get-Content $pinFile -Raw).Trim() -eq $pin)
            if (-not $havePy) {
                Write-Host "`nNo installed Python found. Downloading Python $PyVersion (about 47 MB)..."
                $name = "cpython-$PyVersion%2B$PyRelease-$arch-pc-windows-msvc-install_only.tar.gz"
                $pyTar = Join-Path $Tmp 'python.tar.gz'
                Get-Download "https://github.com/astral-sh/python-build-standalone/releases/download/$PyRelease/$name" $pyTar 'Python'
                if ((Get-Sha256 $pyTar) -ne $PySha256[$arch]) {
                    throw 'The downloaded Python failed its integrity check, so setup was stopped. Try again later.'
                }
                if (Test-Path $pyDir) { Remove-Item -Recurse -Force $pyDir }
                Expand-Tar $pyTar $pyDir
                Set-Content -Path $pinFile -Value $pin -NoNewline -Encoding ASCII
            }
            $python = Join-Path $pyDir 'python.exe'
        }

        # 3) Dependencies as plain files in .deps\ (windows_launcher.py puts this folder on sys.path).
        Write-Host "`nInstalling dependencies (this may take a minute)..."
        $deps = Join-Path $Dir '.deps'
        $req = Join-Path $Dir 'requirements.txt'
        & $python -m pip install -q --disable-pip-version-check --upgrade --target $deps -r $req "comtypes==$ComtypesVersion"
        if ($LASTEXITCODE -ne 0) {
            throw ('Could not install the dependencies. Check your internet/VPN connection and try again. ' +
                   "If the message above says 'No module named pip', this Python has no pip; ask IT for one that does.")
        }
        Set-Content -Path (Join-Path $deps '.req-sha256') -Value (Get-Sha256 $req) -NoNewline -Encoding ASCII
        $oldVenv = Join-Path $Dir '.venv'  # left over from an earlier setup version
        if (Test-Path $oldVenv) { Remove-Item -Recurse -Force $oldVenv -ErrorAction SilentlyContinue }

        # 4) Start menu and desktop shortcuts (pythonw.exe runs the launcher without a console window).
        $launcher = Join-Path $Dir 'windows_launcher.py'
        if ($env:JIRA_WORKLOG_NO_SHORTCUTS -ne '1') {
            & $python $launcher --install-shortcuts
            if ($LASTEXITCODE -ne 0) { throw 'Could not create the shortcuts.' }
        }

        Write-Host "`nSetup complete." -ForegroundColor Green
        Write-Host "Installed in: $Dir"
        Write-Host 'Open "Jira Worklog" from the Start menu or the desktop shortcut.'
        if ($env:JIRA_WORKLOG_NO_LAUNCH -ne '1') {
            Write-Host 'Opening it now...'
            Start-Process -FilePath (Join-Path (Split-Path $python -Parent) 'pythonw.exe') -ArgumentList ('"' + $launcher + '"') -WorkingDirectory $Dir
        }
    } catch {
        $msg = $_.Exception.Message
        Write-Host "`nSetup failed: $msg" -ForegroundColor Red
        if ($msg -match 'group policy|Application Control|AppLocker|blocked') {
            Write-Host ("Your computer's security policy blocked a program. Install Python from your company's " +
                        'software portal, then run this command again: it will use that Python. ' +
                        'If it still fails, ask IT for help.') -ForegroundColor Yellow
        }
        Write-Host "(PowerShell language mode: $($ExecutionContext.SessionState.LanguageMode))"
    } finally {
        if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue }
    }
}

Install-JiraWorklog
