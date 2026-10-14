@echo off
rem Windows: ilk calistirmada kurulum yapar, sonra uygulamayi acar. Cift tiklamak yeterli.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First-time setup in progress, this may take a few minutes...
  py -3 -m venv .venv 2>nul || python -m venv .venv
  if errorlevel 1 (
    echo Python 3.9 or newer was not found. Install it from https://www.python.org/downloads/ and try again.
    pause
    exit /b 1
  )
  ".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt
)
if exist ".git" if not "%JIRA_WORKLOG_NO_UPDATE%"=="1" git pull --ff-only --quiet >nul 2>&1
rem requirements.txt degistiyse bagimliliklari yeniden kur
fc /b requirements.txt ".venv\req.txt" >nul 2>&1 || (".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt && copy /y requirements.txt ".venv\req.txt" >nul)
".venv\Scripts\python.exe" worklog_web.py %*
