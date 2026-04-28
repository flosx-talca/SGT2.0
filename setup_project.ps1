# SGT 2.0 - Project Setup Script (Windows)
# This script automates the installation and configuration of the environment.

Write-Host "--- SGT 2.0: Starting Setup ---" -ForegroundColor Cyan

# 1. Check for Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python is not installed or not in PATH." -ForegroundColor Red
    exit
}

# 2. Create Virtual Environment
if (!(Test-Path "venv")) {
    Write-Host "[1/4] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "[1/4] Virtual environment already exists." -ForegroundColor Gray
}

# 3. Install Dependencies
Write-Host "[2/4] Installing dependencies from requirements.txt..." -ForegroundColor Yellow
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# 4. Database Migrations
Write-Host "[3/4] Running database migrations..." -ForegroundColor Yellow
# Ensure the database exists. The user must have Postgres running.
$env:FLASK_APP = "app"
.\venv\Scripts\python.exe -m flask db upgrade

# 5. Seed Initial Data
Write-Host "[4/4] Seeding initial data (Rules and Legal Parameters)..." -ForegroundColor Yellow
.\venv\Scripts\python.exe run_seed_reglas.py
.\venv\Scripts\python.exe run_seed_parametros_legales.py

Write-Host "`n--- Setup Complete! ---" -ForegroundColor Green
Write-Host "To run the application, use: .\venv\Scripts\python.exe run.py" -ForegroundColor Cyan
