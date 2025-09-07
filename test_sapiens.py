#!/usr/bin/env python3
"""
Test script to verify Sapiens integration
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required packages can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
    except ImportError as e:
        print(f"❌ PyTorch: {e}")
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
        from sapiens_inference import SapiensPredictor, SapiensConfig, SapiensSegmentationType
        print("✅ sapiens-inference")
    except ImportError as e:
        print(f"❌ sapiens-inference: {e}")
        print("💡 Install with: pip install sapiens-inference")
        return False
    
    return True

def test_sapiens_model():
    """Test Sapiens model loading"""
    print("\n🤖 Testing Sapiens model...")
    
    try:
        from sapiens_inference import SapiensPredictor, SapiensConfig, SapiensSegmentationType
        import numpy as np
        
        # Configure Sapiens
        config = SapiensConfig()
        config.segmentation_type = SapiensSegmentationType.SEGMENTATION_1B
        config.device = 'auto'
        
        print("📥 Loading Sapiens-1B model (this may take a while on first run)...")
        predictor = SapiensPredictor(config)
        print("✅ Sapiens model loaded successfully!")
        
        # Test with a dummy image
        dummy_image = np.random.randint(0, 255, (1024, 768, 3), dtype=np.uint8)
        print("🔄 Testing segmentation on dummy image...")
        
        result = predictor(dummy_image)
        print("✅ Segmentation test completed!")
        
        # Check what attributes the result has
        print(f"📊 Result type: {type(result)}")
        if hasattr(result, '__dict__'):
            print(f"📊 Result attributes: {list(result.__dict__.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Sapiens test failed: {e}")
        return False

def test_processor():
    """Test our SapiensProcessor class"""
    print("\n🔧 Testing SapiensProcessor...")
    
    try:
        from sapiens_processor import SapiensProcessor
        
        print("📥 Initializing SapiensProcessor...")
        processor = SapiensProcessor(model_size='1b', device='auto')
        print("✅ SapiensProcessor initialized successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ SapiensProcessor test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Sapiens Integration Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import test failed. Please install missing packages:")
        print("   pip install -r sapiens_requirements.txt")
        sys.exit(1)
    
    # Test Sapiens model
    if not test_sapiens_model():
        print("\n❌ Sapiens model test failed.")
        sys.exit(1)
    
    # Test processor
    if not test_processor():
        print("\n❌ SapiensProcessor test failed.")
        sys.exit(1)
    
    print("\n✅ All tests passed! Sapiens integration is working.")
    print("\n🎯 You can now run the watcher:")
    print("   python sapiens_watcher.py --watch-dir output/captures --output-dir output/sapiens_segmentation")
    print("\n🎯 Or test with a single image:")
    print("   python sapiens_processor.py path/to/image.jpg --output-dir output/sapiens_segmentation")

if __name__ == '__main__':
    main()
