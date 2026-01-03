#!/bin/bash

echo "🚀 Initializing Talus Trace Development Environment..."

# 1. Create Virtual Environment
if [ ! -d "venv" ]; then
    echo "📦 Creating Python Virtual Environment (venv)..."
    python3 -m venv venv
else
    echo "✅ venv already exists."
fi

# 2. Activate & Install
echo "⬇️  Installing Dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Initialize Git
if [ ! -d ".git" ]; then
    echo "🐙 Initializing Git Repository..."
    git init
    git branch -M main
    echo "✅ Git initialized."
else
    echo "✅ Git repository already exists."
fi

# 4. Create Directory Structure (Ensures dev.py works)
echo "ww📂 Creating Project Directories..."
mkdir -p talustrace/backend
mkdir -p talustrace/frontend
mkdir -p talustrace/assets
mkdir -p tests
mkdir -p data

# 5. Create __init__ files to make them packages
touch talustrace/__init__.py
touch talustrace/backend/__init__.py
touch talustrace/frontend/__init__.py

echo "---"
echo "✅ Setup Complete!"
echo "👉 To start working: source venv/bin/activate"