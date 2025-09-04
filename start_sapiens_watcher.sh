#!/bin/bash

echo "🤖 Starting Sapiens Watcher (macOS/Linux)"
echo "========================================"

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    echo "Install with: brew install python3"
    exit 1
fi

echo "✅ Python found: $(python --version)"

# Check if requirements are installed
echo "🔍 Checking Python dependencies..."
python -c "import torch, torchvision, PIL, numpy, watchdog" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip install -r python/requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

# Start the watcher
echo "🚀 Starting Sapiens watcher..."
cd python
python sapiens_watcher.py --captures-dir ../output/captures --output-dir ../output --model-size 1b --device auto
```

```

