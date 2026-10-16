# Jira Worklog setup for Windows. Paste into PowerShell:
#   irm https://raw.githubusercontent.com/aliyetim/jira-worklog/main/install.ps1 | iex
# Downloads the app (~100 KB) and a portable Python (~47 MB) into %LOCALAPPDATA%\jira-worklog and adds
# Start menu and desktop shortcuts. Needs neither Git nor an installed Python, and no administrator rights.
# Running it again is harmless (it updates the app; settings and a saved token are kept).
# Environment: JIRA_WORKLOG_DIR (install folder), JIRA_WORKLOG_NO_SHORTCUTS=1, JIRA_WORKLOG_NO_LAUNCH=1.
#
# Keep this file ASCII-only: Windows PowerShell 5.1 reads files without a BOM as ANSI.
# Everything runs inside a function so that "irm | iex" never closes the user's window on errors.

function Install-JiraWorklog {
    $ErrorActionPreference = 'Stop'
    $ProgressPreference = 'SilentlyContinue'  # Invoke-WebRequest is very slow with the progress bar
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    try { [Net.WebRequest]::DefaultWebProxy.Credentials = [Net.CredentialCache]::DefaultNetworkCredentials } catch { }

    $Repo = 'aliyetim/jira-worklog'
    # Portable Python (python-build-standalone, an official CPython build). The version is pinned and the
    # download is checked against these SHA-256 hashes (from the release's SHA256SUMS file).
    $PyRelease = '20261003'
    $PyVersion = '3.12.15'
    $PySha256 = @{
        'x86_64'  = '4b6f0beebbb695a0f3ea237b8c3eaa5bd424f47a7bc25b2fbe3a43390c770f08'
        'aarch64' = '2de96a340fecdabe215094345ed3aea1b473e858bd098360f2253299e18f24d2'
    }

    $Dir = if ($env:JIRA_WORKLOG_DIR) { $env:JIRA_WORKLOG_DIR } else { Join-Path $env:LOCALAPPDATA 'jira-worklog' }
    $Tmp = Join-Path ([IO.Path]::GetTempPath()) ('jira-worklog-' + [guid]::NewGuid().ToString('N'))
    $Tar = Join-Path $env:SystemRoot 'System32\tar.exe'  # built into Windows 10 1803+; not Git's tar

    function Get-Download([string]$Uri, [string]$OutFile, [string]$What) {
        try {
            Invoke-WebRequest -UseBasicParsing -Uri $Uri -OutFile $OutFile
        } catch {
            throw "Could not download $What. Check your internet/VPN connection and try again. ($($_.Exception.Message))"
        }
    }

    try {
        New-Item -ItemType Directory -Force -Path $Dir, $Tmp | Out-Null
        $Dir = (Resolve-Path $Dir).Path

        # A running copy keeps its files locked; close it first.
        Get-Process pythonw, python -ErrorAction SilentlyContinue |
            Where-Object { $_.Path -and $_.Path.StartsWith($Dir, [StringComparison]::OrdinalIgnoreCase) } |
            ForEach-Object { Write-Host 'Closing the running Jira Worklog app...'; Stop-Process -Id $_.Id -Force }

        # 1) App files. windows_launcher.py checks for updates with the archive's ETag. PowerShell gets a different
        #    (compressed, weak) ETag than Python's urllib, so we store "pending": the first launch fetches the
        #    archive once (~100 KB) and saves the ETag it sees; later launches get 304 and download nothing.
        if (-not (Test-Path (Join-Path $Dir '.git'))) {
            Write-Host "`nDownloading the app..."
            $zip = Join-Path $Tmp 'app.zip'
            Get-Download "https://codeload.github.com/$Repo/zip/refs/heads/main" $zip 'the app' | Out-Null
            Expand-Archive -Path $zip -DestinationPath (Join-Path $Tmp 'app') -Force
            $root = Get-ChildItem (Join-Path $Tmp 'app') -Directory | Select-Object -First 1
            if (-not $root -or -not (Test-Path (Join-Path $root.FullName 'worklog_web.py'))) {
                throw 'The downloaded app archive is damaged. Try again.'
            }
            & robocopy $root.FullName $Dir /E /NFL /NDL /NJH /NJS /NP | Out-Null
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
            Get-Download "https://github.com/astral-sh/python-build-standalone/releases/download/$PyRelease/$name" $pyTar 'Python' | Out-Null
            $hash = (Get-FileHash -Algorithm SHA256 -Path $pyTar).Hash.ToLowerInvariant()
            if ($hash -ne $PySha256[$arch]) {
                throw 'The downloaded Python failed its integrity check, so setup was stopped. Try again later.'
            }
            foreach ($old in @($pyDir, $venvDir)) {  # the environment is tied to the old Python; rebuild it
                if (Test-Path $old) { Remove-Item -Recurse -Force $old }
            }
            New-Item -ItemType Directory -Force -Path $pyDir | Out-Null
            & $Tar -xzf $pyTar -C $pyDir --strip-components=1
            if ($LASTEXITCODE -ne 0) { throw 'Could not unpack Python.' }
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
        & $venvPy -m pip install -q --disable-pip-version-check -r $req
        if ($LASTEXITCODE -ne 0) { throw 'Could not install the dependencies. Check your internet/VPN connection and try again.' }
        $reqHash = (Get-FileHash -Algorithm SHA256 -Path $req).Hash.ToLowerInvariant()
        Set-Content -Path (Join-Path $venvDir '.req-sha256') -Value $reqHash -NoNewline -Encoding ASCII

        # 4) Shortcuts: pythonw.exe runs the launcher without a console window.
        $pythonw = Join-Path $venvDir 'Scripts\pythonw.exe'
        $launcher = Join-Path $Dir 'windows_launcher.py'
        if ($env:JIRA_WORKLOG_NO_SHORTCUTS -ne '1') {
            $shell = New-Object -ComObject WScript.Shell
            foreach ($place in @([Environment]::GetFolderPath('Programs'), [Environment]::GetFolderPath('Desktop'))) {
                $lnk = $shell.CreateShortcut((Join-Path $place 'Jira Worklog.lnk'))
                $lnk.TargetPath = $pythonw
                $lnk.Arguments = '"' + $launcher + '"'
                $lnk.WorkingDirectory = $Dir
                $lnk.IconLocation = (Join-Path $Dir 'assets\icon.ico') + ',0'
                $lnk.Description = 'Jira worklog report'
                $lnk.Save()
            }
        }

        Write-Host "`nSetup complete." -ForegroundColor Green
        Write-Host "Installed in: $Dir"
        Write-Host 'Open "Jira Worklog" from the Start menu or the desktop shortcut.'
        if ($env:JIRA_WORKLOG_NO_LAUNCH -ne '1') {
            Write-Host 'Opening it now...'
            Start-Process -FilePath $pythonw -ArgumentList ('"' + $launcher + '"') -WorkingDirectory $Dir
        }
    } catch {
        Write-Host "`nSetup failed: $($_.Exception.Message)" -ForegroundColor Red
    } finally {
        if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue }
    }
}

Install-JiraWorklog
