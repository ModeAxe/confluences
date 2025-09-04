@echo off
echo �� Setting up Sapiens from Facebook Research
echo =============================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Create sapiens directory
set SAPIENS_DIR=python\sapiens
if not exist "%SAPIENS_DIR%" (
    echo 📥 Cloning Sapiens repository...
    git clone https://github.com/facebookresearch/sapiens.git "%SAPIENS_DIR%"
    if errorlevel 1 (
        echo ❌ Failed to clone Sapiens repository
        pause
        exit /b 1
    )
) else (
    echo ✅ Sapiens directory already exists
)

REM Install Python dependencies
echo 📦 Installing Python dependencies...
pip install -r python\requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install Python dependencies
    pause
    exit /b 1
)

REM Install Sapiens Lite dependencies
echo �� Installing Sapiens Lite dependencies...
cd "%SAPIENS_DIR%\lite"
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install Sapiens Lite dependencies
    pause
    exit /b 1
)

REM Download model if not exists
set MODEL_PATH=sapiens_lite.pth
if not exist "%MODEL_PATH%" (
    echo 📥 Downloading Sapiens Lite model...
    curl -L -o "%MODEL_PATH%" https://huggingface.co/facebook/sapiens/resolve/main/sapiens_lite_host/sapiens_lite.pth
    if errorlevel 1 (
        echo ❌ Failed to download model
        pause
        exit /b 1
    )
) else (
    echo ✅ Model already exists
)

cd ..\..\..

echo.
echo 🎉 Sapiens setup complete!
echo.
echo �� Next steps:
echo 1. Run: python launch_sapiens.py
echo 2. Start your Electron app: npm run dev
echo 3. Capture images - Sapiens will process them automatically

pause
