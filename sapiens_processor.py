#!/usr/bin/env python3
"""
Simple Sapiens Body Segmentation Processor
Uses the Sapiens-Pytorch-Inference library for accurate body part segmentation
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Set
import numpy as np
from PIL import Image
import cv2

# Sapiens imports
try:
    from sapiens_inference import SapiensPredictor, SapiensConfig, SapiensSegmentationType
except ImportError:
    print("❌ Sapiens inference not found. Install with: pip install sapiens-inference")
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SapiensProcessor:
    """Handles Sapiens model loading and image processing"""
    
    # Body part groups for organized output (based on Sapiens segmentation)
    BODY_PART_GROUPS = {
        'head': ['head', 'face', 'hair', 'left_eye', 'right_eye', 'nose', 'mouth', 'left_ear', 'right_ear', 'neck'],
        'left_arm': ['left_shoulder', 'left_arm', 'left_elbow', 'left_forearm', 'left_hand'],
        'right_arm': ['right_shoulder', 'right_arm', 'right_elbow', 'right_forearm', 'right_hand'],
        'torso': ['torso', 'chest', 'back', 'stomach'],
        'left_leg': ['left_hip', 'left_thigh', 'left_knee', 'left_shin', 'left_ankle', 'left_foot'],
        'right_leg': ['right_hip', 'right_thigh', 'right_knee', 'right_shin', 'right_ankle', 'right_foot']
    }
    
    def __init__(self, model_size: str = '1b', device: str = 'auto'):
        """
        Initialize the Sapiens processor
        
        Args:
            model_size: Model size ('0.3b', '0.6b', '1b', '2b')
            device: Device to use ('auto', 'cpu', 'cuda', 'mps')
        """
        self.model_size = model_size
        self.device = device
        self.predictor = None
        self.processed_files: Set[str] = set()
        self._load_model()
    
    def _load_model(self):
        """Load the Sapiens model"""
        try:
            logger.info(f"🤖 Loading Sapiens-{self.model_size} model...")
            
            # Configure Sapiens
            config = SapiensConfig()
            config.segmentation_type = getattr(SapiensSegmentationType, f'SEGMENTATION_{self.model_size.upper()}')
            config.device = self.device
            
            # Initialize predictor
            self.predictor = SapiensPredictor(config)
            
            logger.info(f"✅ Sapiens-{self.model_size} model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Error loading Sapiens model: {e}")
            logger.error("💡 Make sure sapiens-inference is installed: pip install sapiens-inference")
            raise
    
    def segment_image(self, image_path: str) -> Dict:
        """Segment body parts in an image using Sapiens"""
        try:
            # Load image
            image = Image.open(image_path).convert('RGB')
            image_array = np.array(image)
            
            logger.info(f"📸 Processing: {os.path.basename(image_path)} ({image_array.shape[1]}x{image_array.shape[0]})")
            
            # Run Sapiens segmentation
            result = self.predictor(image_array)
            
            # Extract segmentation mask from result
            segmentation_mask = self._extract_segmentation_mask(result)
            
            # Extract individual body parts
            body_parts = self._extract_body_parts(segmentation_mask, image_array.shape)
            
            return {
                'success': True,
                'image_path': image_path,
                'segmentation_mask': segmentation_mask,
                'body_parts': body_parts,
                'total_parts': len(body_parts),
                'model_info': {
                    'model': f'Sapiens-{self.model_size}',
                    'device': self.device
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error segmenting image: {e}")
            return {'success': False, 'error': str(e)}
    
    def _extract_segmentation_mask(self, result) -> np.ndarray:
        """Extract segmentation mask from Sapiens result"""
        try:
            # Sapiens result should contain segmentation information
            if hasattr(result, 'segmentation'):
                return result.segmentation
            elif isinstance(result, dict) and 'segmentation' in result:
                return result['segmentation']
            elif isinstance(result, np.ndarray):
                return result
            else:
                # Try to get the first available mask-like data
                if hasattr(result, 'mask'):
                    return result.mask
                else:
                    raise ValueError("Could not extract segmentation mask from Sapiens result")
        except Exception as e:
            logger.error(f"❌ Error extracting segmentation mask: {e}")
            raise
    
    def _extract_body_parts(self, segmentation_mask: np.ndarray, image_shape: tuple) -> List[Dict]:
        """Extract individual body parts from segmentation mask"""
        body_parts = []
        
        try:
            # Get unique labels in the segmentation
            unique_labels = np.unique(segmentation_mask)
            
            for label in unique_labels:
                if label == 0:  # Skip background
                    continue
                
                # Create mask for this body part
                part_mask = (segmentation_mask == label).astype(np.uint8) * 255
                
                # Count pixels
                pixel_count = np.sum(part_mask > 0)
                
                if pixel_count > 100:  # Only include parts with significant pixels
                    # Map label to body part name (simplified mapping)
                    part_name = self._map_label_to_part_name(label)
                    group = self._get_part_group(part_name)
                    
                    body_parts.append({
                        'name': part_name,
                        'label_id': int(label),
                        'pixel_count': int(pixel_count),
                        'mask': part_mask,
                        'group': group
                    })
            
            return body_parts
            
        except Exception as e:
            logger.error(f"❌ Error extracting body parts: {e}")
            return []
    
    def _map_label_to_part_name(self, label: int) -> str:
        """Map Sapiens label to body part name"""
        # Simplified mapping - in practice, you'd use the actual Sapiens label mapping
        label_mapping = {
            1: 'head',
            2: 'torso',
            3: 'left_arm',
            4: 'right_arm',
            5: 'left_leg',
            6: 'right_leg',
            7: 'left_hand',
            8: 'right_hand',
            9: 'left_foot',
            10: 'right_foot'
        }
        return label_mapping.get(label, f'part_{label}')
    
    def _get_part_group(self, part_name: str) -> str:
        """Determine which group a body part belongs to"""
        for group_name, parts in self.BODY_PART_GROUPS.items():
            if part_name in parts:
                return group_name
        return 'other'
    
    def save_segmentation(self, image_path: str, output_dir: str, result: Dict) -> bool:
        """Save segmentation results organized by body parts"""
        if not result['success']:
            return False
        
        try:
            # Create output directory structure
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for each body part group
            for group_name in self.BODY_PART_GROUPS.keys():
                (output_path / group_name).mkdir(parents=True, exist_ok=True)
            
            base_name = Path(image_path).stem
            saved_files = []
            
            # Save each body part to its respective folder
            for part_info in result['body_parts']:
                part_name = part_info['name']
                part_mask = part_info['mask']
                group = part_info['group']
                
                # Create colored mask for better visualization
                colored_mask = self._create_colored_mask(part_mask, part_name)
                
                # Save to appropriate folder
                output_file = output_path / group / f"{part_name}_{base_name}.png"
                colored_mask.save(output_file)
                
                saved_files.append(str(output_file))
                logger.info(f"💾 Saved {part_name} to: {output_file}")
            
            # Also save the full segmentation mask
            full_mask_path = output_path / f"{base_name}_full_segmentation.png"
            cv2.imwrite(str(full_mask_path), result['segmentation_mask'])
            saved_files.append(str(full_mask_path))
            
            logger.info(f"✅ Saved {len(saved_files)} files for {base_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving segmentation: {e}")
            return False
    
    def _create_colored_mask(self, mask: np.ndarray, part_name: str) -> Image.Image:
        """Create a colored mask for a body part"""
        # Generate a consistent color for this body part
        color = self._get_part_color(part_name)
        
        # Create RGB image
        colored_mask = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
        colored_mask[mask > 0] = color
        
        return Image.fromarray(colored_mask)
    
    def _get_part_color(self, part_name: str) -> tuple:
        """Generate a consistent color for a body part"""
        # Simple hash-based color generation
        hash_val = hash(part_name) % 360
        hue = hash_val / 360.0
        
        # Convert HSV to RGB
        import colorsys
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
        return tuple(int(c * 255) for c in rgb)

def main():
    """Test the Sapiens processor"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sapiens Body Segmentation Processor')
    parser.add_argument('image_path', help='Path to input image')
    parser.add_argument('--output-dir', default='output/sapiens_segmentation', 
                       help='Output directory for segmentation results')
    parser.add_argument('--model-size', default='1b', choices=['0.3b', '0.6b', '1b', '2b'],
                       help='Sapiens model size')
    parser.add_argument('--device', default='auto', choices=['auto', 'cpu', 'cuda', 'mps'],
                       help='Device to use for inference')
    
    args = parser.parse_args()
    
    # Check if image exists
    if not os.path.exists(args.image_path):
        print(f"❌ Error: Image file not found: {args.image_path}")
        return
    
    try:
        # Initialize processor
        processor = SapiensProcessor(model_size=args.model_size, device=args.device)
        
        # Process image
        result = processor.segment_image(args.image_path)
        
        if result['success']:
            print(f"✅ Segmentation completed!")
            print(f"📊 Found {result['total_parts']} body parts")
            print(f"🤖 Model: {result['model_info']['model']} on {result['model_info']['device']}")
            
            # Save results
            save_success = processor.save_segmentation(args.image_path, args.output_dir, result)
            
            if save_success:
                print(f"💾 Results saved to: {args.output_dir}")
            else:
                print("❌ Failed to save results")
        else:
            print(f"❌ Segmentation failed: {result['error']}")
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == '__main__':
    main()
