@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 -B "%~dp0blackwing_launcher.py" %*
exit /b %errorlevel%
:use_python
python -B "%~dp0blackwing_launcher.py" %*
exit /b %errorlevel%
