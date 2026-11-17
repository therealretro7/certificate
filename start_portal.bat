@echo off
title Google Student Ambassador Certificate Portal
echo ================================================================
echo Starting Google Student Ambassador Certificate Portal...
echo ================================================================
cd /d "%~dp0"

REM Try python from Mocha Pro or PATH
set PYTHON_EXE="C:\Program Files\BorisFX\Mocha Pro 2023\python\python.exe"
if not exist %PYTHON_EXE% (
    set PYTHON_EXE=python
)

echo Starting backend server on http://localhost:8000
start "" http://localhost:8000
%PYTHON_EXE% server.py
pause

