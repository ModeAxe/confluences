#!/bin/bash

echo "�� Setting up Sapiens from Facebook Research"
echo "============================================="

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python found: $(python --version)"

# Create sapiens directory
SAPIENS_DIR="python/sapiens"
if [ ! -d "$SAPIENS_DIR" ]; then
    echo "📥 Cloning Sapiens repository..."
    git clone https://github.com/facebookresearch/sapiens.git "$SAPIENS_DIR"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to clone Sapiens repository"
        exit 1
    fi
else
    echo "✅ Sapiens directory already exists"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r python/requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

# Install Sapiens Lite dependencies
echo "�� Installing Sapiens Lite dependencies..."
cd "$SAPIENS_DIR/lite"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Sapiens Lite dependencies"
    exit 1
fi

# Download model if not exists
MODEL_PATH="sapiens_lite.pth"
if [ ! -f "$MODEL_PATH" ]; then
    echo "📥 Downloading Sapiens Lite model..."
    wget https://huggingface.co/facebook/sapiens/resolve/main/sapiens_lite_host/sapiens_lite.pth
    if [ $? -ne 0 ]; then
        echo "❌ Failed to download model"
        exit 1
    fi
else
    echo "✅ Model already exists"
fi

cd ../../..

echo ""
echo "🎉 Sapiens setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Run: python launch_sapiens.py"
echo "2. Start your Electron app: npm run dev"
echo "3. Capture images - Sapiens will process them automatically"
