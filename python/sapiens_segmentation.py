#!/usr/bin/env python3
"""
Sapiens Body-Part Segmentation Service
Uses Facebook Research Sapiens Lite for body-part segmentation
"""

import sys
import os
import json
import argparse
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
from torchvision import transforms
import cv2

# Add Sapiens Lite to path
SAPIENS_LITE_PATH = Path(__file__).parent / 'sapiens' / 'lite'
if SAPIENS_LITE_PATH.exists():
    sys.path.insert(0, str(SAPIENS_LITE_PATH))

try:
    from sapiens_lite import SapiensLite
except ImportError:
    print("❌ Sapiens Lite not found. Please run setup_sapiens.sh first.")
    print("   This will clone the repository and install dependencies.")
    sys.exit(1)

# Sapiens body part classes (based on Sapiens Lite output)
SAPIENS_BODY_PARTS = {
    0: 'background',
    1: 'hair',
    2: 'face',
    3: 'left_eye',
    4: 'right_eye',
    5: 'nose',
    6: 'mouth',
    7: 'upper_lip',
    8: 'lower_lip',
    9: 'teeth',
    10: 'tongue',
    11: 'left_ear',
    12: 'right_ear',
    13: 'neck',
    14: 'left_shoulder',
    15: 'right_shoulder',
    16: 'left_arm',
    17: 'right_arm',
    18: 'left_elbow',
    19: 'right_elbow',
    20: 'left_forearm',
    21: 'right_forearm',
    22: 'left_hand',
    23: 'right_hand',
    24: 'torso',
    25: 'left_hip',
    26: 'right_hip',
    27: 'left_thigh',
    28: 'right_thigh',
    29: 'left_knee',
    30: 'right_knee',
    31: 'left_shin',
    32: 'right_shin',
    33: 'left_ankle',
    34: 'right_ankle',
    35: 'left_foot',
    36: 'right_foot'
}

# Group body parts for organized output - SPLIT ARMS INTO LEFT AND RIGHT
BODY_PART_GROUPS = {
    'head': ['hair', 'face', 'left_eye', 'right_eye', 'nose', 'mouth', 'upper_lip', 'lower_lip', 'teeth', 'tongue', 'left_ear', 'right_ear', 'neck'],
    'left_arm': ['left_shoulder', 'left_arm', 'left_elbow', 'left_forearm', 'left_hand'],
    'right_arm': ['right_shoulder', 'right_arm', 'right_elbow', 'right_forearm', 'right_hand'],
    'torso': ['torso'],
    'left_leg': ['left_hip', 'left_thigh', 'left_knee', 'left_shin', 'left_ankle', 'left_foot'],
    'right_leg': ['right_hip', 'right_thigh', 'right_knee', 'right_shin', 'right_ankle', 'right_foot']
}

class SapiensSegmentationService:
    def __init__(self, model_path: str = None, device: str = 'auto'):
        """
        Initialize the Sapiens segmentation service
        
        Args:
            model_path: Path to the Sapiens Lite model
            device: Device to run inference on ('auto', 'cpu', 'cuda')
        """
        self.device = self._get_device(device)
        self.model = None
        self.model_path = model_path or str(SAPIENS_LITE_PATH / 'sapiens_lite.pth')
        self._load_model()
    
    def _get_device(self, device: str) -> str:
        """Determine the best device to use"""
        if device == 'auto':
            if torch.cuda.is_available():
                return 'cuda'
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return 'mps'  # Apple Silicon
            else:
                return 'cpu'
        return device
    
    def _load_model(self):
        """Load the Sapiens Lite model"""
        try:
            print(f"🤖 Loading Sapiens Lite model from: {self.model_path}")
            
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
            # Initialize Sapiens Lite
            self.model = SapiensLite(model_path=self.model_path, device=self.device)
            print(f"✅ Sapiens Lite model loaded successfully on {self.device}")
            
        except Exception as e:
            print(f"❌ Error loading Sapiens Lite model: {e}")
            print("💡 Make sure you've run setup_sapiens.sh to download the model")
            raise
    
    def segment_image(self, image_path: str) -> Dict:
        """
        Perform body-part segmentation on an image
        
        Args:
            image_path: Path to the input image
            
        Returns:
            Dictionary containing segmentation results
        """
        start_time = time.time()
        
        try:
            # Load image
            image = Image.open(image_path).convert('RGB')
            original_size = image.size
            
            print(f"📸 Processing image: {original_size[0]}x{original_size[1]}")
            
            # Run segmentation using Sapiens Lite
            segmentation_result = self.model.segment_person_parts(image)
            
            # Extract segmentation mask
            if isinstance(segmentation_result, dict):
                segmentation_mask = segmentation_result.get('segmentation', segmentation_result.get('mask'))
            else:
                segmentation_mask = segmentation_result
            
            if segmentation_mask is None:
                raise ValueError("No segmentation mask returned from model")
            
            # Convert to numpy if needed
            if torch.is_tensor(segmentation_mask):
                segmentation_mask = segmentation_mask.cpu().numpy()
            
            # Extract individual body parts
            body_parts = self._extract_body_parts(segmentation_mask, original_size)
            
            processing_time = time.time() - start_time
            
            result = {
                'success': True,
                'original_size': original_size,
                'processing_time': processing_time,
                'body_parts': body_parts,
                'total_parts_found': len(body_parts),
                'model_info': {
                    'model': 'Sapiens Lite',
                    'device': self.device
                }
            }
            
            print(f"✅ Segmentation completed in {processing_time:.2f}s")
            print(f"📊 Found {len(body_parts)} body parts")
            
            return result
            
        except Exception as e:
            print(f"❌ Error during segmentation: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _extract_body_parts(self, segmentation_mask: np.ndarray, original_size: Tuple[int, int]) -> List[Dict]:
        """Extract individual body parts from segmentation mask"""
        body_parts = []
        
        # Get unique labels in the segmentation
        unique_labels = np.unique(segmentation_mask)
        
        for label in unique_labels:
            if label == 0:  # Skip background
                continue
                
            part_name = SAPIENS_BODY_PARTS.get(label, f'unknown_{label}')
            
            # Create mask for this body part
            part_mask = (segmentation_mask == label).astype(np.uint8) * 255
            
            # Count pixels
            pixel_count = np.sum(part_mask > 0)
            
            if pixel_count > 0:  # Only include parts with pixels
                body_parts.append({
                    'name': part_name,
                    'label_id': int(label),
                    'pixel_count': int(pixel_count),
                    'mask_size': original_size,
                    'group': self._get_part_group(part_name)
                })
        
        return body_parts
    
    def _get_part_group(self, part_name: str) -> str:
        """Determine which group a body part belongs to"""
        for group_name, parts in BODY_PART_GROUPS.items():
            if part_name in parts:
                return group_name
        return 'other'
    
    def save_segmentation_masks(self, image_path: str, output_dir: str, segmentation_result: Dict) -> Dict:
        """
        Save individual body part masks as images
        
        Args:
            image_path: Path to the original image
            output_dir: Directory to save masks
            segmentation_result: Result from segment_image()
            
        Returns:
            Dictionary with save results
        """
        if not segmentation_result['success']:
            return {'success': False, 'error': 'Segmentation failed'}
        
        try:
            # Create output directories
            output_path = Path(output_dir)
            for group in BODY_PART_GROUPS.keys():
                (output_path / group).mkdir(parents=True, exist_ok=True)
            
            # Load original image and get full segmentation
            image = Image.open(image_path).convert('RGB')
            segmentation_result_full = self.model.segment_person_parts(image)
            
            # Extract segmentation mask
            if isinstance(segmentation_result_full, dict):
                segmentation_mask = segmentation_result_full.get('segmentation', segmentation_result_full.get('mask'))
            else:
                segmentation_mask = segmentation_result_full
            
            if torch.is_tensor(segmentation_mask):
                segmentation_mask = segmentation_mask.cpu().numpy()
            
            saved_files = []
            base_filename = Path(image_path).stem
            
            # Save each body part
            for part_info in segmentation_result['body_parts']:
                part_name = part_info['name']
                label_id = part_info['label_id']
                group = part_info['group']
                
                # Create mask for this part
                part_mask = (segmentation_mask == label_id).astype(np.uint8) * 255
                
                # Create colored mask
                colored_mask = self._create_colored_mask(part_mask, part_name)
                
                # Save mask
                output_file = output_path / group / f"{part_name}_{base_filename}.png"
                colored_mask.save(output_file)
                
                saved_files.append(str(output_file))
                print(f"💾 Saved {part_name} to: {output_file}")
            
            return {
                'success': True,
                'saved_files': saved_files,
                'total_saved': len(saved_files)
            }
            
        except Exception as e:
            print(f"❌ Error saving masks: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_colored_mask(self, mask: np.ndarray, part_name: str) -> Image.Image:
        """Create a colored mask for a body part"""
        # Generate a consistent color for this body part
        color = self._get_part_color(part_name)
        
        # Create RGB image
        colored_mask = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
        colored_mask[mask > 0] = color
        
        return Image.fromarray(colored_mask)
    
    def _get_part_color(self, part_name: str) -> Tuple[int, int, int]:
        """Generate a consistent color for a body part"""
        # Simple hash-based color generation
        hash_val = hash(part_name) % 360
        hue = hash_val / 360.0
        
        # Convert HSV to RGB
        import colorsys
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
        return tuple(int(c * 255) for c in rgb)

def main():
    parser = argparse.ArgumentParser(description='Sapiens Body-Part Segmentation')
    parser.add_argument('image_path', help='Path to input image')
    parser.add_argument('--output-dir', default='output', help='Output directory for masks')
    parser.add_argument('--model-path', help='Path to Sapiens Lite model')
    parser.add_argument('--device', default='auto', choices=['auto', 'cpu', 'cuda', 'mps'],
                       help='Device to run inference on')
    parser.add_argument('--save-masks', action='store_true', help='Save individual body part masks')
    
    args = parser.parse_args()
    
    # Check if image exists
    if not os.path.exists(args.image_path):
        print(f"❌ Error: Image file not found: {args.image_path}")
        sys.exit(1)
    
    try:
        # Initialize service
        service = SapiensSegmentationService(
            model_path=args.model_path,
            device=args.device
        )
        
        # Perform segmentation
        result = service.segment_image(args.image_path)
        
        # Print results
        print("\n" + "="*50)
        print("SAPIENS SEGMENTATION RESULTS")
        print("="*50)
        
        if result['success']:
            print(f"✅ Success!")
            print(f"⏱️  Processing time: {result['processing_time']:.2f}s")
            print(f"📊 Body parts found: {result['total_parts_found']}")
            print(f"🤖 Model: {result['model_info']['model']} on {result['model_info']['device']}")
            
            print("\n📋 Body Parts:")
            for part in result['body_parts']:
                print(f"  • {part['name']} ({part['group']}) - {part['pixel_count']} pixels")
            
            # Save masks if requested
            if args.save_masks:
                print(f"\n Saving masks to: {args.output_dir}")
                save_result = service.save_segmentation_masks(args.image_path, args.output_dir, result)
                
                if save_result['success']:
                    print(f"✅ Saved {save_result['total_saved']} body part masks")
                else:
                    print(f"❌ Error saving masks: {save_result['error']}")
            
            # Output JSON for Electron app
            print("\n📤 JSON Output:")
            print(json.dumps(result, indent=2))
            
        else:
            print(f"❌ Segmentation failed: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
