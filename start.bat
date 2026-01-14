@echo off
echo ========================================
echo ARAS - Access Recertification Demo
echo ========================================
echo.

REM Check for .env file or API key
if exist ".env" (
    echo Found .env file - API key will be loaded from there.
) else if "%ANTHROPIC_API_KEY%"=="" (
    echo Warning: Chat assistant requires ANTHROPIC_API_KEY.
    echo.
    echo Option 1: Create a .env file in the project root:
    echo           copy .env.example .env
    echo           Then edit .env and add your API key.
    echo.
    echo Option 2: Set in this CMD window before running:
    echo           set ANTHROPIC_API_KEY=your_key
    echo           start.bat
    echo.
    echo Note: PowerShell $env: variables do NOT transfer to batch files.
    echo.
)

echo Starting Backend API on http://localhost:8000...
start "ARAS Backend" cmd /k "python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000"

timeout /t 5 /nobreak >nul

echo Starting Frontend on http://localhost:3000...
start "ARAS Frontend" cmd /k "cd frontend && npm run dev -- --port 3000"

echo.
echo ========================================
echo ARAS is starting up!
echo ----------------------------------------
echo Backend API:  http://localhost:8000
echo API Docs:     http://localhost:8000/api/docs
echo Frontend:     http://localhost:3000
echo ========================================
echo.
echo Press any key to open the frontend in your browser...
pause >nul
start http://localhost:3000
