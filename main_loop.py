# main_loop.py
import os
import time
import logging
import json
import threading
import queue
from pathlib import Path
from wxauto import WXAuto
from homework import HomeworkProcessor
from env import EnvConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class MainLoopProcessor:
    def __init__(self, env_file=".env"):
        self._config = EnvConfig(env_file)
        self.wxauto = WXAuto(env_file)
        self.homework_processor = HomeworkProcessor(env_file)
        self.download_path = self._get_download_path()
        self.running = False
        
        # Message queue for async processing
        self.message_queue = queue.Queue()
        self.processing_threads = []
        self.max_workers = 3  # Maximum concurrent processing threads
        
    def _get_download_path(self):
        """Get download path from environment"""
        download_path = self._config.get('WXAUTO_DOWNLOAD_PATH')
        if not download_path:
            # Default download path
            download_path = "/tmp/wxauto_download"
        
        path = Path(download_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created download directory: {path}")
        
        return path
    
    def extract_image_messages(self, message_result):
        """
        Extract image messages from message result
        
        Args:
            message_result (dict): Result from get_next_new_message
            
        Returns:
            list: List of image messages with file paths
        """
        if not message_result.get("success") or not message_result.get("has_message"):
            return []
        
        image_messages = []
        for msg in message_result.get("messages", []):
            if (msg.get("type") == "image" and 
                msg.get("class") == "FriendImageMessage" and
                msg.get("download_success") == True and
                msg.get("file_name")):
                
                # Build full file path
                file_name = msg.get("file_name")
                file_path = self.download_path / file_name
                
                if file_path.exists():
                    image_messages.append({
                        "chat_name": msg.get("chat_name"),
                        "file_name": file_name,
                        "file_path": str(file_path),
                        "message_id": msg.get("id"),
                        "raw_message": msg
                    })
                    logger.info(f"Found image message: {file_name}")
                else:
                    logger.warning(f"Image file not found: {file_path}")
        
        return image_messages
    
    def process_single_image_async(self, image_msg):
        """
        Process a single image message asynchronously
        
        Args:
            image_msg (dict): Image message data
        """
        try:
            logger.info(f"Async processing started for: {image_msg['file_name']}")
            
            # Process each image with OCR using homework processor
            ocr_result = self.homework_processor.process_image_with_ocr(
                image_path=image_msg['file_path'],
                chat_name=image_msg['chat_name']
            )
            
            # Handle the OCR result using homework processor
            self.homework_processor.handle_ocr_result(
                ocr_result=ocr_result,
                wxauto_client=self.wxauto
            )
            
            logger.info(f"Async processing completed for: {image_msg['file_name']}")
            
        except Exception as e:
            logger.error(f"Error in async processing for {image_msg['file_name']}: {str(e)}")
    
    def process_message_batch_async(self, message_result):
        """
        Process a batch of messages asynchronously
        
        Args:
            message_result (dict): Result from get_next_new_message
        """
        if not message_result.get("success"):
            logger.error(f"Failed to get messages: {message_result.get('error')}")
            return
        
        if not message_result.get("has_message"):
            # No new messages
            return
        
        chat_name = message_result.get("chat_name")
        logger.info(f"Processing messages from: {chat_name}")
        
        # Extract and process image messages
        image_messages = self.extract_image_messages(message_result)
        
        for image_msg in image_messages:
            # Start async processing for each image
            thread = threading.Thread(
                target=self.process_single_image_async,
                args=(image_msg,),
                daemon=True
            )
            thread.start()
            self.processing_threads.append(thread)
            
            # Limit the number of concurrent threads
            if len(self.processing_threads) >= self.max_workers:
                # Wait for some threads to complete before starting new ones
                self._cleanup_finished_threads()
    
    def _cleanup_finished_threads(self):
        """Remove finished threads from the list"""
        self.processing_threads = [t for t in self.processing_threads if t.is_alive()]
    
    def message_listener_loop(self, check_interval=3):
        """
        Main message listener loop - runs in main thread
        
        Args:
            check_interval (int): Interval between checks in seconds
        """
        logger.info("Starting message listener loop...")
        
        try:
            while self.running:
                # Get new messages
                message_result = self.wxauto.get_next_new_message()
                
                # Process the messages asynchronously
                self.process_message_batch_async(message_result)
                
                # Clean up finished threads
                self._cleanup_finished_threads()
                
                # Wait before next check
                time.sleep(check_interval)
                
        except Exception as e:
            logger.error(f"Error in message listener loop: {str(e)}")
            raise
    
    def main_loop(self, check_interval=3):
        """
        Main processing loop with async processing
        
        Args:
            check_interval (int): Interval between checks in seconds
        """
        self.running = True
        logger.info("Starting main loop with async processing...")
        logger.info(f"Download path: {self.download_path}")
        logger.info(f"Check interval: {check_interval}s")
        logger.info(f"Max concurrent workers: {self.max_workers}")
        
        try:
            # Start the message listener loop
            self.message_listener_loop(check_interval)
                
        except KeyboardInterrupt:
            logger.info("Main loop interrupted by user")
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
        finally:
            self.running = False
            logger.info("Main loop stopped")
            
            # Wait for all processing threads to complete
            self._wait_for_all_threads()
    
    def _wait_for_all_threads(self):
        """Wait for all processing threads to complete"""
        logger.info("Waiting for all processing threads to complete...")
        for thread in self.processing_threads:
            if thread.is_alive():
                thread.join(timeout=10)  # Wait up to 10 seconds for each thread
        logger.info("All processing threads completed")
    
    def stop(self):
        """Stop the main loop"""
        self.running = False
        logger.info("Stopping main loop...")
        self._wait_for_all_threads()


def main():
    """Main function"""
    print("Starting Main Loop Processor with Async Processing...")
    
    # Create processor instance
    processor = MainLoopProcessor()
    
    # Start main loop
    try:
        processor.main_loop(check_interval=3)
    except Exception as e:
        logger.error(f"Failed to start main loop: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()