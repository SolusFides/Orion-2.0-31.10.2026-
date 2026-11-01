@echo off
where docker >nul 2>nul
if errorlevel 1 (
  echo Error: docker is not installed.
  exit /b 1
)

cd /d "%~dp0"
if not exist api_gateway\.env copy api_gateway\.env.example api_gateway\.env >nul

echo Building and starting Orion Home...
docker compose up -d --build

echo.
echo Local machine is up!
echo.
echo You can check API docs at: http://localhost:8000/docs
echo.
echo Command to down all containers:
echo local_down.bat
echo.
