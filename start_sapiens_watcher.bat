@echo off
echo 🤖 Starting Sapiens Watcher (Windows)
echo =====================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Check if requirements are installed
echo 🔍 Checking Python dependencies...
python -c "import torch, torchvision, PIL, numpy, watchdog" >nul 2>&1
if errorlevel 1 (
    echo ❌ Missing dependencies. Installing...
    pip install -r python/requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Start the watcher
echo 🚀 Starting Sapiens watcher...
cd python
python sapiens_watcher.py --captures-dir ../output/captures --output-dir ../output --model-size 1b --device auto

pause
