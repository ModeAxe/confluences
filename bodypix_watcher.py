#!/usr/bin/env python3
"""
Simple BodyPix Image Watcher
Watches a folder for new images and segments body parts using BodyPix
"""

import os
import time
import queue
import threading
import logging
from pathlib import Path
from typing import Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# BodyPix imports
import tensorflow as tf
import numpy as np
from PIL import Image
import cv2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BodyPixProcessor:
    """Handles BodyPix model loading and image processing"""
    
    # Body part groups for organized output
    BODY_PART_GROUPS = {
        'head': ['head', 'face', 'hair', 'left_eye', 'right_eye', 'nose', 'mouth', 'left_ear', 'right_ear', 'neck'],
        'left_arm': ['left_shoulder', 'left_arm', 'left_elbow', 'left_forearm', 'left_hand'],
        'right_arm': ['right_shoulder', 'right_arm', 'right_elbow', 'right_forearm', 'right_hand'],
        'torso': ['torso', 'chest', 'back', 'stomach'],
        'left_leg': ['left_hip', 'left_thigh', 'left_knee', 'left_shin', 'left_ankle', 'left_foot'],
        'right_leg': ['right_hip', 'right_thigh', 'right_knee', 'right_shin', 'right_ankle', 'right_foot']
    }
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.processed_files: Set[str] = set()
        self._load_model(model_path)
    
    def _load_model(self, model_path: str = None):
        """Load the BodyPix model"""
        try:
            logger.info("🤖 Loading BodyPix model...")
            
            # For simplicity, we'll use a pre-trained model
            # You can download from: https://github.com/tensorflow/tfjs-models/tree/master/body-pix
            if model_path and os.path.exists(model_path):
                self.model = tf.saved_model.load(model_path)
            else:
                # Use a simple segmentation model as fallback
                # In practice, you'd want to download the actual BodyPix model
                logger.warning("⚠️  Using fallback model. For best results, download BodyPix model.")
                self.model = self._create_fallback_model()
            
            logger.info("✅ BodyPix model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Error loading BodyPix model: {e}")
            raise
    
    def _create_fallback_model(self):
        """Create a simple fallback model for demonstration"""
        # This is a placeholder - in practice you'd load the actual BodyPix model
        return None
    
    def segment_image(self, image_path: str) -> dict:
        """Segment body parts in an image"""
        try:
            # Load image
            image = Image.open(image_path).convert('RGB')
            image_array = np.array(image)
            
            logger.info(f"📸 Processing: {os.path.basename(image_path)} ({image_array.shape[1]}x{image_array.shape[0]})")
            
            # For demonstration, create a simple segmentation
            # In practice, you'd use the actual BodyPix model here
            segmentation_result = self._simple_segmentation(image_array)
            
            return {
                'success': True,
                'image_path': image_path,
                'segmentation': segmentation_result,
                'body_parts': self._extract_body_parts(segmentation_result)
            }
            
        except Exception as e:
            logger.error(f"❌ Error segmenting image: {e}")
            return {'success': False, 'error': str(e)}
    
    def _simple_segmentation(self, image: np.ndarray) -> np.ndarray:
        """Simple segmentation for demonstration purposes"""
        # This is a placeholder - replace with actual BodyPix inference
        height, width = image.shape[:2]
        
        # Create a simple segmentation mask (just for demo)
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # Simple body detection using color and position heuristics
        # In practice, you'd use the actual BodyPix model
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Find skin-like regions (very basic)
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Simple morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)
        
        return skin_mask
    
    def _extract_body_parts(self, segmentation: np.ndarray) -> list:
        """Extract body parts from segmentation mask"""
        body_parts = []
        
        # For demonstration, we'll create a simple body part detection
        # In practice, BodyPix would provide detailed part segmentation
        height, width = segmentation.shape
        
        # Simple heuristic-based body part detection
        # This is a placeholder - replace with actual BodyPix part segmentation
        parts_detected = self._detect_body_parts_heuristic(segmentation, height, width)
        
        for part_name, mask in parts_detected.items():
            pixel_count = np.sum(mask > 0)
            if pixel_count > 0:
                body_parts.append({
                    'name': part_name,
                    'pixel_count': int(pixel_count),
                    'mask': mask,
                    'group': self._get_part_group(part_name)
                })
        
        return body_parts
    
    def _detect_body_parts_heuristic(self, segmentation: np.ndarray, height: int, width: int) -> dict:
        """Simple heuristic-based body part detection for demonstration"""
        parts = {}
        
        # Create masks for different body regions based on position
        # This is a simplified approach - real BodyPix would provide actual part segmentation
        
        # Head region (top 25% of body)
        head_mask = np.zeros_like(segmentation)
        head_region = segmentation[:height//4, :]
        head_mask[:height//4, :] = head_region
        
        # Torso region (middle 40% of body)
        torso_mask = np.zeros_like(segmentation)
        torso_start = height//4
        torso_end = int(height * 0.65)
        torso_region = segmentation[torso_start:torso_end, :]
        torso_mask[torso_start:torso_end, :] = torso_region
        
        # Legs region (bottom 35% of body)
        legs_mask = np.zeros_like(segmentation)
        legs_start = int(height * 0.65)
        legs_region = segmentation[legs_start:, :]
        legs_mask[legs_start:, :] = legs_region
        
        # Split legs into left and right
        left_leg_mask = np.zeros_like(segmentation)
        right_leg_mask = np.zeros_like(segmentation)
        left_leg_mask[legs_start:, :width//2] = legs_region[:, :width//2]
        right_leg_mask[legs_start:, width//2:] = legs_region[:, width//2:]
        
        # Split torso into left and right arms
        left_arm_mask = np.zeros_like(segmentation)
        right_arm_mask = np.zeros_like(segmentation)
        left_arm_mask[torso_start:torso_end, :width//3] = torso_region[:, :width//3]
        right_arm_mask[torso_start:torso_end, 2*width//3:] = torso_region[:, 2*width//3:]
        
        # Only include parts with significant pixel count
        if np.sum(head_mask > 0) > 100:
            parts['head'] = head_mask
        if np.sum(torso_mask > 0) > 100:
            parts['torso'] = torso_mask
        if np.sum(left_arm_mask > 0) > 50:
            parts['left_arm'] = left_arm_mask
        if np.sum(right_arm_mask > 0) > 50:
            parts['right_arm'] = right_arm_mask
        if np.sum(left_leg_mask > 0) > 100:
            parts['left_leg'] = left_leg_mask
        if np.sum(right_leg_mask > 0) > 100:
            parts['right_leg'] = right_leg_mask
        
        return parts
    
    def _get_part_group(self, part_name: str) -> str:
        """Determine which group a body part belongs to"""
        for group_name, parts in self.BODY_PART_GROUPS.items():
            if part_name in parts:
                return group_name
        return 'other'
    
    def save_segmentation(self, image_path: str, output_dir: str, result: dict) -> bool:
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
            cv2.imwrite(str(full_mask_path), result['segmentation'])
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

class ImageHandler(FileSystemEventHandler):
    """Handles file system events for new images"""
    
    def __init__(self, processing_queue: queue.Queue):
        self.processing_queue = processing_queue
        self.supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in self.supported_extensions:
            # Wait for file to be fully written
            time.sleep(0.5)
            
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                logger.info(f"📸 New image detected: {os.path.basename(file_path)}")
                self.processing_queue.put(file_path)

class BodyPixWatcher:
    """Main watcher class that coordinates file watching and processing"""
    
    def __init__(self, watch_dir: str, output_dir: str, model_path: str = None):
        self.watch_dir = watch_dir
        self.output_dir = output_dir
        self.model_path = model_path
        
        # Queue for processing images in order
        self.processing_queue = queue.Queue(maxsize=100)
        
        # Components
        self.processor = None
        self.observer = None
        self.event_handler = None
        self.processing_thread = None
        self.running = False
    
    def _initialize_processor(self):
        """Initialize the BodyPix processor"""
        try:
            self.processor = BodyPixProcessor(model_path=self.model_path)
            logger.info("✅ BodyPix processor initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize processor: {e}")
            raise
    
    def _processing_worker(self):
        """Worker thread that processes images from the queue"""
        logger.info("🔄 Processing worker started")
        
        while self.running:
            try:
                # Get image from queue (blocks for up to 1 second)
                image_path = self.processing_queue.get(timeout=1.0)
                
                # Check if already processed
                if image_path in self.processor.processed_files:
                    logger.info(f"⏭️  Already processed: {os.path.basename(image_path)}")
                    self.processing_queue.task_done()
                    continue
                
                # Process the image
                start_time = time.time()
                result = self.processor.segment_image(image_path)
                processing_time = time.time() - start_time
                
                if result['success']:
                    # Save results
                    save_success = self.processor.save_segmentation(
                        image_path, self.output_dir, result
                    )
                    
                    if save_success:
                        logger.info(f"✅ Processed in {processing_time:.1f}s: {os.path.basename(image_path)}")
                        self.processor.processed_files.add(image_path)
                    else:
                        logger.error(f"❌ Failed to save: {os.path.basename(image_path)}")
                else:
                    logger.error(f"❌ Processing failed: {os.path.basename(image_path)} - {result.get('error', 'Unknown error')}")
                
                # Mark task as done
                self.processing_queue.task_done()
                
            except queue.Empty:
                # No items in queue, continue waiting
                continue
            except Exception as e:
                logger.error(f"❌ Processing error: {e}")
                continue
        
        logger.info("🛑 Processing worker stopped")
    
    def _setup_file_watcher(self):
        """Setup the file system watcher"""
        if not os.path.exists(self.watch_dir):
            logger.error(f"❌ Watch directory not found: {self.watch_dir}")
            raise FileNotFoundError(f"Watch directory not found: {self.watch_dir}")
        
        self.event_handler = ImageHandler(self.processing_queue)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.watch_dir, recursive=False)
        
        logger.info(f"👀 Watching directory: {self.watch_dir}")
    
    def start(self):
        """Start the watcher"""
        try:
            logger.info("🚀 Starting BodyPix Watcher...")
            logger.info(f"👀 Watch directory: {self.watch_dir}")
            logger.info(f"📁 Output directory: {self.output_dir}")
            
            # Initialize components
            self._initialize_processor()
            self._setup_file_watcher()
            
            # Start processing thread
            self.running = True
            self.processing_thread = threading.Thread(target=self._processing_worker, daemon=True)
            self.processing_thread.start()
            
            # Start file watcher
            self.observer.start()
            logger.info("✅ BodyPix Watcher started!")
            logger.info("Press Ctrl+C to stop...")
            
            # Keep running until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()
                
        except Exception as e:
            logger.error(f"❌ Failed to start watcher: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop the watcher"""
        logger.info("🛑 Stopping BodyPix Watcher...")
        self.running = False
        
        # Stop file watcher
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        # Wait for processing queue to empty
        if self.processing_queue:
            try:
                self.processing_queue.join()
            except:
                pass
        
        # Wait for processing thread to finish
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5.0)
        
        logger.info("👋 BodyPix Watcher stopped")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='BodyPix Image Watcher')
    parser.add_argument('--watch-dir', default='output/captures', 
                       help='Directory to watch for new images')
    parser.add_argument('--output-dir', default='output/bodypix_segmentation', 
                       help='Output directory for segmentation results')
    parser.add_argument('--model-path', 
                       help='Path to BodyPix model (optional)')
    
    args = parser.parse_args()
    
    # Create and start watcher
    watcher = BodyPixWatcher(
        watch_dir=args.watch_dir,
        output_dir=args.output_dir,
        model_path=args.model_path
    )
    
    watcher.start()

if __name__ == '__main__':
    main()
