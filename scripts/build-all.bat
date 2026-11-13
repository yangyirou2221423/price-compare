@echo off
set "ROOT=%~dp0.."
where node >nul 2>nul
if errorlevel 1 set "PATH=%ROOT%\tools\node-v22.23.5-win-x64;%PATH%"
cd /d "%ROOT%\frontend"
call npm.cmd run build:h5
if errorlevel 1 exit /b %errorlevel%
call npm.cmd run build:mp-weixin
