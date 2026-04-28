#!/bin/bash

# SGT 2.0 - Project Setup Script (Linux/macOS)
# This script automates the installation and configuration of the environment.

echo -e "\e[36m--- SGT 2.0: Starting Setup ---\e[0m"

# 1. Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "\e[31mError: python3 is not installed or not in PATH.\e[0m"
    exit 1
fi

# 2. Create Virtual Environment
if [ ! -d "venv" ]; then
    echo -e "\e[33m[1/4] Creating virtual environment...\e[0m"
    python3 -m venv venv
else
    echo -e "\e[90m[1/4] Virtual environment already exists.\e[0m"
fi

# 3. Install Dependencies
echo -e "\e[33m[2/4] Installing dependencies from requirements.txt...\e[0m"
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 4. Database Migrations
echo -e "\e[33m[3/4] Running database migrations...\e[0m"
export FLASK_APP=app
./venv/bin/python -m flask db upgrade

# 5. Seed Initial Data
echo -e "\e[33m[4/4] Seeding initial data (Rules and Legal Parameters)...\e[0m"
./venv/bin/python run_seed_reglas.py
./venv/bin/python run_seed_parametros_legales.py

echo -e "\n\e[32m--- Setup Complete! ---\e[0m"
echo -e "\e[36mTo run the application, use: ./venv/bin/python run.py\e[0m"
