@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "ROOT="
call :try_root "%SCRIPT_DIR%"
call :try_root "%SCRIPT_DIR%\TechSpar"
call :try_root "%CD%"
call :try_root "%CD%\TechSpar"
call :try_root "c:\Users\Administrator\Desktop\26面试\TechSpar"

if not defined ROOT (
  echo Could not locate TechSpar project root.
  echo Expected a directory containing backend\main.py and frontend\package.json.
  pause
  exit /b 1
)

set "BACKEND_HOST=127.0.0.1"
set "BACKEND_PORT=8000"
set "FRONTEND_HOST=127.0.0.1"
set "FRONTEND_PORT=5173"
set "FRONTEND_URL=http://127.0.0.1:%FRONTEND_PORT%"
set "SHOULD_OPEN_BROWSER=1"

echo Using TechSpar root: "%ROOT%"

call :is_port_listening "%BACKEND_PORT%"
if not errorlevel 1 set "SHOULD_OPEN_BROWSER=0"
call :is_port_listening "%FRONTEND_PORT%"
if not errorlevel 1 set "SHOULD_OPEN_BROWSER=0"

call :restart_if_running "TechSpar backend" "%BACKEND_PORT%"
if errorlevel 1 (
  pause
  exit /b 1
)

echo Starting TechSpar backend...
start "TechSpar Backend" cmd /k "cd /d ""%ROOT%"" && python -m uvicorn backend.main:app --host %BACKEND_HOST% --port %BACKEND_PORT%"

echo Waiting for backend on %BACKEND_PORT%...
call :wait_http_ready "http://%BACKEND_HOST%:%BACKEND_PORT%/api/auth/config" "60"
if errorlevel 1 (
  echo Backend did not become ready within 60 seconds.
  echo Please check the backend window for errors.
  pause
  exit /b 1
)

call :restart_if_running "TechSpar frontend" "%FRONTEND_PORT%"
if errorlevel 1 (
  pause
  exit /b 1
)

echo Starting TechSpar frontend...
start "TechSpar Frontend" cmd /k "cd /d ""%ROOT%\frontend"" && npm run dev -- --host %FRONTEND_HOST% --port %FRONTEND_PORT%"

echo Waiting for frontend on %FRONTEND_PORT%...
call :wait_http_ready "http://%FRONTEND_HOST%:%FRONTEND_PORT%/" "60"
if errorlevel 1 (
  echo Frontend did not become ready within 60 seconds.
  echo Please check the frontend window for errors.
  pause
  exit /b 1
)

if "%SHOULD_OPEN_BROWSER%"=="1" (
  echo Opening browser: %FRONTEND_URL%
  start "" "%FRONTEND_URL%"
) else (
  echo Browser launch skipped because backend or frontend was already running.
)

echo All services started.
exit /b 0

:restart_if_running
set "SERVICE_NAME=%~1"
set "SERVICE_PORT=%~2"

call :is_port_listening "%SERVICE_PORT%"
if errorlevel 1 (
  echo %SERVICE_NAME% is not running on port %SERVICE_PORT%, starting fresh.
  exit /b 0
)

echo %SERVICE_NAME% is already running on port %SERVICE_PORT%, restarting it...
call :stop_port_process "%SERVICE_PORT%"
if errorlevel 1 (
  echo Failed to stop %SERVICE_NAME% on port %SERVICE_PORT%.
  exit /b 1
)

call :wait_port_closed "%SERVICE_PORT%" "30"
if errorlevel 1 (
  echo %SERVICE_NAME% did not release port %SERVICE_PORT% within 30 seconds.
  exit /b 1
)

exit /b 0

:stop_port_process
set "TARGET_PORT=%~1"
set "FOUND_PID="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%TARGET_PORT% .*LISTENING"') do (
  set "FOUND_PID=1"
  echo Stopping PID %%P on port %TARGET_PORT%...
  taskkill /PID %%P /F >nul 2>&1
  if errorlevel 1 (
    echo Failed to terminate PID %%P on port %TARGET_PORT%.
    exit /b 1
  )
)
if not defined FOUND_PID (
  echo No listening process found on port %TARGET_PORT%.
  exit /b 1
)
exit /b 0

:is_port_listening
netstat -ano | findstr /R /C:":%~1 .*LISTENING" >nul 2>&1
exit /b %errorlevel%

:wait_port_open
set "WAIT_PORT=%~1"
set /a WAIT_SECONDS=%~2
set /a WAIT_ELAPSED=0
:wait_port_open_loop
call :is_port_listening "%WAIT_PORT%"
if not errorlevel 1 exit /b 0
if !WAIT_ELAPSED! GEQ !WAIT_SECONDS! exit /b 1
timeout /t 1 /nobreak >nul
set /a WAIT_ELAPSED+=1
goto :wait_port_open_loop

:is_http_ready
powershell -NoProfile -Command "try { $response = Invoke-WebRequest -UseBasicParsing -Uri '%~1' -TimeoutSec 5; if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
exit /b %errorlevel%

:wait_http_ready
set "WAIT_URL=%~1"
set /a WAIT_SECONDS=%~2
set /a WAIT_ELAPSED=0
:wait_http_ready_loop
call :is_http_ready "%WAIT_URL%"
if not errorlevel 1 exit /b 0
if !WAIT_ELAPSED! GEQ !WAIT_SECONDS! exit /b 1
timeout /t 1 /nobreak >nul
set /a WAIT_ELAPSED+=1
goto :wait_http_ready_loop

:wait_port_closed
set "WAIT_PORT=%~1"
set /a WAIT_SECONDS=%~2
set /a WAIT_ELAPSED=0
:wait_port_closed_loop
call :is_port_listening "%WAIT_PORT%"
if errorlevel 1 exit /b 0
if !WAIT_ELAPSED! GEQ !WAIT_SECONDS! exit /b 1
timeout /t 1 /nobreak >nul
set /a WAIT_ELAPSED+=1
goto :wait_port_closed_loop

:try_root
if defined ROOT exit /b 0
set "CANDIDATE=%~f1"
if exist "%CANDIDATE%\backend\main.py" if exist "%CANDIDATE%\frontend\package.json" set "ROOT=%CANDIDATE%"
exit /b 0
