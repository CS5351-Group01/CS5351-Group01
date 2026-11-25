@echo off
REM Double-click this file to start the demo server and open the browser.
REM It just calls scripts\start-demo.ps1 with the execution policy bypassed.

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\start-demo.ps1"
if errorlevel 1 pause
