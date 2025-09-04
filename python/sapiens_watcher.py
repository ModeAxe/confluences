#!/usr/bin/env python3
"""
Sapiens Watcher - Watches Syncthing folder for new images
"""

import os
import time
import sys
import queue
import threading
import logging
import platform
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sapiens_segmentation import SapiensSegmentationService

def setup_logging():
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / 'sapiens_watcher.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class ImageProcessor:
    def __init__(self, output_dir: str, model_size: str = '1b', device: str = 'auto'):
        self.output_dir = output_dir
        self.service = None
        self.model_size = model_size
        self.device = device
        self.processed_files = set()
        self._initialize_service()
    
    def _initialize_service(self):
        try:
            logger.info(f"🤖 Initializing Sapiens-{self.model_size} model...")
            self.service = SapiensSegmentationService(
                model_size=self.model_size,
                device=self.device
            )
            logger.info("✅ Sapiens service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Sapiens service: {e}")
            raise
    
    def process_image(self, image_path: str) -> bool:
        if image_path in self.processed_files:
            return True
        
        try:
            logger.info(f"🔄 Processing: {os.path.basename(image_path)}")
            start_time = time.time()
            
            result = self.service.segment_image(image_path)
            
            if not result['success']:
                logger.error(f"❌ Segmentation failed: {result['error']}")
                return False
            
            save_result = self.service.save_segmentation_masks(
                image_path, self.output_dir, result
            )
            
            if not save_result['success']:
                logger.error(f"❌ Failed to save masks: {save_result['error']}")
                return False
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Completed in {processing_time:.1f}s - {result['total_parts_found']} body parts")
            
            self.processed_files.add(image_path)
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing {image_path}: {e}")
            return False

class ImageHandler(FileSystemEventHandler):
    def __init__(self, processing_queue: queue.Queue):
        self.processing_queue = processing_queue
        self.supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in self.supported_extensions:
            time.sleep(0.5)  # Wait for file to be fully written
            
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                logger.info(f"📸 New image: {os.path.basename(file_path)}")
                self.processing_queue.put(file_path)

class SapiensWatcher:
    def __init__(self, watch_dir: str, output_dir: str, model_size: str = '1b', device: str = 'auto'):
        self.watch_dir = watch_dir
        self.output_dir = output_dir
        self.model_size = model_size
        self.device = device
        self.processing_queue = queue.Queue(maxsize=100)
        self.processor = None
        self.observer = None
        self.event_handler = None
        self.processing_thread = None
        self.running = False
    
    def _initialize_processor(self):
        try:
            self.processor = ImageProcessor(
                output_dir=self.output_dir,
                model_size=self.model_size,
                device=self.device
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize processor: {e}")
            raise
    
    def _processing_worker(self):
        logger.info("🔄 Processing worker started")
        
        while self.running:
            try:
                image_path = self.processing_queue.get(timeout=1.0)
                success = self.processor.process_image(image_path)
                
                if success:
                    logger.info(f"✅ Processed: {os.path.basename(image_path)}")
                else:
                    logger.error(f"❌ Failed: {os.path.basename(image_path)}")
                
                self.processing_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Processing error: {e}")
                continue
        
        logger.info("🛑 Processing worker stopped")
    
    def _setup_file_watcher(self):
        if not os.path.exists(self.watch_dir):
            logger.error(f"❌ Watch directory not found: {self.watch_dir}")
            raise FileNotFoundError(f"Watch directory not found: {self.watch_dir}")
        
        self.event_handler = ImageHandler(self.processing_queue)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.watch_dir, recursive=False)
        logger.info(f"👀 Watching: {self.watch_dir}")
    
    def start(self):
        try:
            logger.info("🚀 Starting Sapiens Watcher...")
            logger.info(f"💻 Platform: {platform.system()}")
            logger.info(f"👀 Watch: {self.watch_dir}")
            logger.info(f"📁 Output: {self.output_dir}")
            logger.info(f"🤖 Model: Sapiens-{self.model_size}")
            
            self._initialize_processor()
            self._setup_file_watcher()
            
            self.running = True
            self.processing_thread = threading.Thread(target=self._processing_worker, daemon=True)
            self.processing_thread.start()
            
            self.observer.start()
            logger.info("✅ Sapiens Watcher started!")
            logger.info("Press Ctrl+C to stop...")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()
                
        except Exception as e:
            logger.error(f"❌ Failed to start: {e}")
            self.stop()
            raise
    
    def stop(self):
        logger.info("🛑 Stopping Sapiens Watcher...")
        self.running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        if self.processing_queue:
            try:
                self.processing_queue.join()
            except:
                pass
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5.0)
        
        logger.info("👋 Stopped")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Sapiens Watcher - Watches Syncthing folder')
    parser.add_argument('--watch-dir', default='Confluences/captures', 
                       help='Syncthing folder to watch')
    parser.add_argument('--output-dir', default='output', 
                       help='Output directory for body parts')
    parser.add_argument('--model-size', default='1b', choices=['0.3b', '0.6b', '1b', '2b'])
    parser.add_argument('--device', default='auto', choices=['auto', 'cpu', 'cuda', 'mps'])
    
    args = parser.parse_args()
    
    watcher = SapiensWatcher(
        watch_dir=args.watch_dir,
        output_dir=args.output_dir,
        model_size=args.model_size,
        device=args.device
    )
    
    watcher.start()

if __name__ == '__main__':
    main()
