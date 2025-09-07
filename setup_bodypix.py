#!/usr/bin/env python3
"""
Setup script for BodyPix Watcher
"""

import os
import sys
import subprocess
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "bodypix_requirements.txt"
        ])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    # Main directories
    directories = [
        "output/captures",
        "output/bodypix_segmentation"
    ]
    
    # Body part subdirectories
    body_parts = [
        "output/bodypix_segmentation/head",
        "output/bodypix_segmentation/left_arm", 
        "output/bodypix_segmentation/right_arm",
        "output/bodypix_segmentation/torso",
        "output/bodypix_segmentation/left_leg",
        "output/bodypix_segmentation/right_leg"
    ]
    
    all_directories = directories + body_parts
    
    for directory in all_directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")

def download_bodypix_model():
    """Download BodyPix model (placeholder)"""
    print("🤖 BodyPix model setup...")
    print("⚠️  Note: This script uses a simplified segmentation approach.")
    print("   For full BodyPix functionality, you'll need to download the actual model.")
    print("   Visit: https://github.com/tensorflow/tfjs-models/tree/master/body-pix")

def main():
    """Main setup function"""
    print("🚀 Setting up BodyPix Watcher...")
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Model setup
    download_bodypix_model()
    
    print("\n✅ Setup complete!")
    print("\nTo run the watcher:")
    print("  python bodypix_watcher.py --watch-dir output/captures --output-dir output/bodypix_segmentation")
    print("\nTo watch a different directory:")
    print("  python bodypix_watcher.py --watch-dir /path/to/your/images")

if __name__ == '__main__':
    main()
