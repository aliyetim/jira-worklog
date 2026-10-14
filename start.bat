@echo off
rem Windows: ilk calistirmada kurulum yapar, sonra uygulamayi acar. Cift tiklamak yeterli.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Ilk kurulum yapiliyor, birkac dakika surebilir...
  py -3 -m venv .venv 2>nul || python -m venv .venv
  if errorlevel 1 (
    echo Python 3.9 veya ustu bulunamadi. https://www.python.org/downloads/ adresinden kurup tekrar deneyin.
    pause
    exit /b 1
  )
  ".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt
)
if exist ".git" if not "%JIRA_WORKLOG_NO_UPDATE%"=="1" git pull --ff-only --quiet >nul 2>&1
".venv\Scripts\python.exe" worklog_web.py %*
