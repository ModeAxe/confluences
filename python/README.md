# Sapiens Segmentation Setup

This directory contains the Python-based Sapiens segmentation system that works on both Windows and macOS.

## Quick Start

### Option 1: Cross-Platform Launcher (Recommended)
```bash
# From the project root directory
python launch_sapiens.py
```

### Option 2: Platform-Specific Scripts

**Windows:**
```cmd
start_sapiens_watcher.bat
```

**macOS/Linux:**
```bash
chmod +x start_sapiens_watcher.sh
./start_sapiens_watcher.sh
```

## Prerequisites

### Windows
1. Install Python 3.8+ from [python.org](https://www.python.org/downloads/)
2. Make sure to check "Add Python to PATH" during installation

### macOS
1. Install Python 3.8+ using Homebrew:
   ```bash
   brew install python3
   ```
2. Or download from [python.org](https://www.python.org/downloads/)

## What It Does

1. **Watches** the `output/captures/` folder for new images
2. **Processes** each image with Sapiens segmentation (36 body parts)
3. **Saves** individual body part masks to organized folders:
   - `head/` - Face, eyes, nose, mouth, etc.
   - `left_arm/` - Left shoulder, arm, elbow, hand
   - `right_arm/` - Right shoulder, arm, elbow, hand
   - `torso/` - Torso
   - `left_leg/` - Left hip, thigh, knee, foot
   - `right_leg/` - Right hip, thigh, knee, foot

## Configuration

Edit the startup scripts to change:
- **Model size**: `0.3b`, `0.6b`, `1b`, `2b` (default: `1b`)
- **Device**: `auto`, `cpu`, `cuda`, `mps` (default: `auto`)
- **Directories**: Change input/output paths as needed

## Logs

Logs are saved to `python/logs/sapiens_watcher.log` for troubleshooting.

## Troubleshooting

### Common Issues

1. **"Python not found"**
   - Windows: Reinstall Python with "Add to PATH" checked
   - macOS: Install with `brew install python3`

2. **"Module not found"**
   - Run: `pip install -r python/requirements.txt`

3. **"CUDA not available"**
   - Install PyTorch with CUDA support
   - Or use `--device cpu` flag

4. **"Permission denied"**
   - macOS: `chmod +x start_sapiens_watcher.sh`
   - Windows: Run as Administrator if needed

### Performance Tips

- **GPU**: Use `--device cuda` for NVIDIA GPUs
- **Apple Silicon**: Use `--device mps` for M1/M2 Macs
- **CPU**: Use `--device cpu` for CPU-only processing
- **Model size**: Use `0.3b` for faster processing, `2b` for best quality

## Integration

The watcher runs independently of your Electron app:
1. Start the watcher: `python launch_sapiens.py`
2. Run your Electron app: `npm run dev`
3. Capture images normally - Sapiens processes them automatically
