@echo off
REM Database Manager Batch Script for Windows
REM Quick commands for database operations

setlocal enabledelayedexpansion

if "%1"=="" (
    echo.
    echo Flight Booking System - Database Manager
    echo ========================================
    echo.
    echo Usage: database_manager.bat [command] [options]
    echo.
    echo Commands:
    echo   export      - Export database to CSV
    echo   setup       - Setup fresh database
    echo   import      - Import from CSV
    echo   full-setup  - Complete workflow
    echo.
    echo Examples:
    echo   database_manager.bat setup
    echo   database_manager.bat export --output ./backup
    echo   database_manager.bat full-setup
    echo.
    echo For more help: python database_manager.py --help
    echo.
    exit /b 0
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.12+
    exit /b 1
)

REM Run the Python script
python database_manager.py %*
