#!/usr/bin/env python3
"""
Test script to verify BodyPix integration
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required packages can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import tensorflow as tf
        print(f"✅ TensorFlow: {tf.__version__}")
    except ImportError as e:
        print(f"❌ TensorFlow: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
    except ImportError as e:
        print(f"❌ NumPy: {e}")
        return False
    
    try:
        from PIL import Image
        print("✅ Pillow (PIL)")
    except ImportError as e:
        print(f"❌ Pillow: {e}")
        return False
    
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
    except ImportError as e:
        print(f"❌ OpenCV: {e}")
        return False
    
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        print("✅ Watchdog")
    except ImportError as e:
        print(f"❌ Watchdog: {e}")
        return False
    
    try:
        from bodypix import BodyPix
        print("✅ tf-bodypix")
    except ImportError as e:
        print(f"❌ tf-bodypix: {e}")
        print("💡 Install with: pip install tf-bodypix")
        return False
    
    return True

def test_bodypix_model():
    """Test BodyPix model loading"""
    print("\n🤖 Testing BodyPix model...")
    
    try:
        from bodypix import BodyPix
        import numpy as np
        
        # Initialize BodyPix (this will download the model if needed)
        print("📥 Loading BodyPix model (this may take a while on first run)...")
        model = BodyPix()
        print("✅ BodyPix model loaded successfully!")
        
        # Test with a dummy image
        dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        print("🔄 Testing segmentation on dummy image...")
        
        result = model.predict_single(dummy_image)
        print("✅ Segmentation test completed!")
        
        # Check what attributes the result has
        print(f"📊 Result attributes: {dir(result)}")
        
        return True
        
    except Exception as e:
        print(f"❌ BodyPix test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 BodyPix Integration Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import test failed. Please install missing packages:")
        print("   pip install -r bodypix_requirements.txt")
        sys.exit(1)
    
    # Test BodyPix model
    if not test_bodypix_model():
        print("\n❌ BodyPix model test failed.")
        sys.exit(1)
    
    print("\n✅ All tests passed! BodyPix integration is working.")
    print("\n🎯 You can now run the watcher:")
    print("   python bodypix_watcher.py --watch-dir output/captures --output-dir output/bodypix_segmentation")

if __name__ == '__main__':
    main()
