@echo off
setlocal
set ELECTRON_RUN_AS_NODE=1
if defined CSDM_PROFILE set "USERPROFILE=%CSDM_PROFILE%"
"%~dp0cs-demo-manager.exe" "%~dp0cscoach-cli.mjs" %*
exit /b %errorlevel%
