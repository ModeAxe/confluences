#!/usr/bin/env python3
"""
Simple Sapiens Image Watcher
Watches a folder for new images and segments body parts using Sapiens
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

# Import our Sapiens processor
from sapiens_processor import SapiensProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

class SapiensWatcher:
    """Main watcher class that coordinates file watching and processing"""
    
    def __init__(self, watch_dir: str, output_dir: str, model_size: str = '1b', device: str = 'auto'):
        self.watch_dir = watch_dir
        self.output_dir = output_dir
        self.model_size = model_size
        self.device = device
        
        # Queue for processing images in order
        self.processing_queue = queue.Queue(maxsize=100)
        
        # Components
        self.processor = None
        self.observer = None
        self.event_handler = None
        self.processing_thread = None
        self.running = False
    
    def _initialize_processor(self):
        """Initialize the Sapiens processor"""
        try:
            self.processor = SapiensProcessor(model_size=self.model_size, device=self.device)
            logger.info("✅ Sapiens processor initialized")
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
                        logger.info(f"✅ Processed in {processing_time:.1f}s: {os.path.basename(image_path)} ({result['total_parts']} parts)")
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
            logger.info("🚀 Starting Sapiens Watcher...")
            logger.info(f"👀 Watch directory: {self.watch_dir}")
            logger.info(f"📁 Output directory: {self.output_dir}")
            logger.info(f"🤖 Model: Sapiens-{self.model_size}")
            logger.info(f"💻 Device: {self.device}")
            
            # Initialize components
            self._initialize_processor()
            self._setup_file_watcher()
            
            # Start processing thread
            self.running = True
            self.processing_thread = threading.Thread(target=self._processing_worker, daemon=True)
            self.processing_thread.start()
            
            # Start file watcher
            self.observer.start()
            logger.info("✅ Sapiens Watcher started!")
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
        logger.info("🛑 Stopping Sapiens Watcher...")
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
        
        logger.info("👋 Sapiens Watcher stopped")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sapiens Image Watcher')
    parser.add_argument('--watch-dir', default='output/captures', 
                       help='Directory to watch for new images')
    parser.add_argument('--output-dir', default='output/sapiens_segmentation', 
                       help='Output directory for segmentation results')
    parser.add_argument('--model-size', default='1b', choices=['0.3b', '0.6b', '1b', '2b'],
                       help='Sapiens model size')
    parser.add_argument('--device', default='auto', choices=['auto', 'cpu', 'cuda', 'mps'],
                       help='Device to use for inference')
    
    args = parser.parse_args()
    
    # Create and start watcher
    watcher = SapiensWatcher(
        watch_dir=args.watch_dir,
        output_dir=args.output_dir,
        model_size=args.model_size,
        device=args.device
    )
    
    watcher.start()

if __name__ == '__main__':
    main()
