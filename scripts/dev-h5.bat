@echo off
set "ROOT=%~dp0.."
where node >nul 2>nul
if errorlevel 1 set "PATH=%ROOT%\tools\node-v22.23.5-win-x64;%PATH%"
cd /d "%ROOT%\frontend"
call npm.cmd run dev:h5 -- --host 127.0.0.1 --port 5173
