@echo off
REM ASCII-only batch file (no Cyrillic) to avoid codepage issues in cmd.exe
setlocal

REM %~dp0 = folder where this .bat lives (project root)
cd /d "%~dp0"

echo.
echo  ==================================================
echo    BURMALDA GPT  -  start all services
echo  ==================================================
echo.

REM --- Check that python and npm are in PATH ---
where python >nul 2>&1
if errorlevel 1 (
  echo [X] Python not found in PATH. Install Python 3.11+ and add it to PATH.
  pause
  exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 (
  echo [X] npm not found in PATH. Install Node.js 18+.
  pause
  exit /b 1
)
echo [OK] Python and npm found.

REM --- First run: install frontend deps if missing ---
if not exist "%~dp0frontend\node_modules" (
  echo.
  echo [*] Installing frontend dependencies ^(first run^)...
  cmd /c "npm --prefix "%~dp0frontend" install"
  if errorlevel 1 (
    echo [X] Failed to install frontend dependencies.
    pause
    exit /b 1
  )
)

REM --- Create backend\.env from example if it does not exist yet ---
if not exist "%~dp0backend\.env" (
  if exist "%~dp0backend\.env.example" (
    copy "%~dp0backend\.env.example" "%~dp0backend\.env" >nul
    echo [*] Created backend\.env from .env.example ^(set your SECRET_KEY^)
  )
)

echo.
echo  Starting services in separate windows...
echo.

REM --- 1. Translator (Burmalda API) -- port 8000 ---
start "BurmaldaGPT - Translator (8000)" /D "%~dp0burmalda_api" cmd /k "python main.py"

REM --- 2. Backend (FastAPI) -- port 8001 ---
start "BurmaldaGPT - Backend (8001)" /D "%~dp0backend" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port 8001"

REM --- 3. Frontend (Vite) -- port 5173 ---
start "BurmaldaGPT - Frontend (5173)" /D "%~dp0frontend" cmd /k "npm run dev"

echo  Waiting 7 seconds for services to start, then opening browser...
timeout /t 7 /nobreak >nul
start "" "http://localhost:5173"

echo.
echo  ==================================================
echo   Done! Open  http://localhost:5173
echo  --------------------------------------------------
echo    Translator  http://localhost:8000
echo    Backend      http://localhost:8001  (docs: /docs)
echo    Frontend     http://localhost:5173
echo  --------------------------------------------------
echo   To stop: close the three service windows
echo   or press Ctrl+C in each of them.
echo  ==================================================
echo.
echo  You can close this window - services keep running.
pause
endlocal
