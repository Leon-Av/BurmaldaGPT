@echo off
REM ASCII-only batch file (no Cyrillic) to avoid codepage issues in cmd.exe
echo.
echo  ==================================================
echo    Stopping BurmaldaGPT services...
echo  ==================================================
echo.

REM Stop processes listening on ports 8000, 8001, 5173 via netstat.
for %%P in (8000 8001 5173) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":%%P " ^| findstr "LISTENING"') do (
    echo  - port %%P: PID %%A
    taskkill /F /PID %%A >nul 2>&1
  )
)

echo.
echo  All services stopped.
echo.
pause
