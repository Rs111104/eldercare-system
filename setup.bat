@echo off
REM ElderCare System - Quick Setup Script for Windows
REM This script automates the initial setup of the ElderCare monitoring system

setlocal enabledelayedexpansion

REM Colors are limited in Windows, so we'll use text instead
echo.
echo ========================================
echo ElderCare System - Initial Setup
echo ========================================
echo.

REM Check if Docker is installed
echo Checking prerequisites...
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo X Docker is NOT installed
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo + Docker is installed

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo X Docker Compose is NOT installed
    pause
    exit /b 1
)
echo + Docker Compose is installed

REM Check if Git is installed
git --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo X Git is NOT installed
    echo Please install Git from https://git-scm.com/
    pause
    exit /b 1
)
echo + Git is installed

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo X Python is NOT installed
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)
echo + Python is installed

REM Check if Node.js is installed
node --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo X Node.js is NOT installed
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
echo + Node.js is installed

echo.
echo + All prerequisites are installed!
echo.

REM Check if in project directory
if not exist "docker-compose.yml" (
    echo X docker-compose.yml not found!
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

REM Environment setup
echo.
echo ========================================
echo Setting Up Environment
echo ========================================
echo.

if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo + Created .env from .env.example
        echo.
        echo ! IMPORTANT: Edit .env with your credentials
        echo ! Required variables:
        echo   - SUPABASE_URL
        echo   - SUPABASE_KEY
        echo   - OPENAI_API_KEY
        echo   - WHATSAPP_API_TOKEN
        echo   - JWT_SECRET
        echo.
        echo Press Enter once you've edited .env...
        pause
    ) else (
        echo X Neither .env nor .env.example found
        pause
        exit /b 1
    )
) else (
    echo + .env already exists
)

REM Build Docker images
echo.
echo ========================================
echo Building Docker Images
echo ========================================
echo.

echo This may take several minutes...
docker-compose build
if %ERRORLEVEL% neq 0 (
    echo X Failed to build Docker images
    pause
    exit /b 1
)

echo.
echo + Docker images built successfully
echo.

REM Start containers
echo.
echo ========================================
echo Starting Containers
echo ========================================
echo.

docker-compose up -d
if %ERRORLEVEL% neq 0 (
    echo X Failed to start containers
    pause
    exit /b 1
)

echo + Containers started successfully
timeout /t 5 /nobreak

REM Check container status
echo.
echo ========================================
echo Container Status
echo ========================================
echo.

docker-compose ps

REM Wait for services
echo.
echo ========================================
echo Waiting for Services to Be Ready
echo ========================================
echo.

echo Checking API health...
setlocal enabledelayedexpansion
set RETRY_COUNT=0
set MAX_RETRIES=30

:retry_loop
if !RETRY_COUNT! geq !MAX_RETRIES! (
    goto retry_done
)

curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo + Backend API is ready!
    goto retry_done
)

set /a RETRY_COUNT=!RETRY_COUNT!+1
echo Attempt !RETRY_COUNT!/!MAX_RETRIES!... waiting for backend...
timeout /t 2 /nobreak
goto retry_loop

:retry_done

REM Verify services
echo.
echo ========================================
echo Service Verification
echo ========================================
echo.

echo Backend API: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo Database: Configured in .env
echo.

REM Final summary
echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.

echo Next steps:
echo 1. Access the API: http://localhost:8000
echo 2. View API docs: http://localhost:8000/docs
echo 3. Access frontend: http://localhost:3000
echo 4. Check logs: docker-compose logs -f
echo 5. Run tests: docker-compose exec backend pytest
echo 6. Stop services: docker-compose down
echo.

echo For detailed documentation, see:
echo - README.md - Project overview
echo - docs/DEPLOYMENT.md - Deployment guide
echo - docs/API.md - API reference
echo - README.md - Start here
echo.

echo + System is running and ready for development!
echo.

pause
