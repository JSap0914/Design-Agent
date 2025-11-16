@echo off
REM ============================================================================
REM Design Agent - Startup Script
REM ============================================================================
REM This script starts the Design Agent job listener
REM ============================================================================

echo.
echo ========================================
echo  Starting Design Agent
echo ========================================
echo.

REM Change to Design Agent directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure it.
    pause
    exit /b 1
)

echo [2/3] Environment configured
echo.

REM Start Design Agent job listener
echo [3/3] Starting Design Agent job listener...
echo.
echo ========================================
echo  Design Agent is running!
echo  Listening for jobs on shared.design_jobs
echo  Press Ctrl+C to stop
echo ========================================
echo.

python -m src.workers.job_listener

REM If job listener exits, pause to see error
pause
