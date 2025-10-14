# main_loop.py
import os
import time
import logging
import json
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
    
    def process_single_image(self, image_msg):
        """
        Process a single image message synchronously
        
        Args:
            image_msg (dict): Image message data
            
        Returns:
            bool: True if processing successful, False otherwise
        """
        try:
            logger.info(f"Processing image: {image_msg['file_name']}")
            
            # Process each image with OCR using homework processor
            ocr_result = self.homework_processor.process_image_with_ocr(
                image_path=image_msg['file_path'],
                chat_name=image_msg['chat_name']
            )
            
            # Handle the OCR result using homework processor
            success = self.homework_processor.handle_ocr_result(
                ocr_result=ocr_result,
                wxauto_client=self.wxauto
            )
            
            if success:
                logger.info(f"Successfully processed image: {image_msg['file_name']}")
            else:
                logger.warning(f"Failed to process image: {image_msg['file_name']}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing {image_msg['file_name']}: {str(e)}")
            return False
    
    def process_message_batch(self, message_result):
        """
        Process a batch of messages synchronously
        
        Args:
            message_result (dict): Result from get_next_new_message
            
        Returns:
            int: Number of images processed
        """
        if not message_result.get("success"):
            logger.error(f"Failed to get messages: {message_result.get('error')}")
            return 0
        
        if not message_result.get("has_message"):
            # No new messages
            return 0
        
        chat_name = message_result.get("chat_name")
        logger.info(f"Processing messages from: {chat_name}")
        
        # Extract image messages
        image_messages = self.extract_image_messages(message_result)
        
        # Process each image synchronously
        processed_count = 0
        for image_msg in image_messages:
            success = self.process_single_image(image_msg)
            if success:
                processed_count += 1
        
        # Also process voice messages if any
        voice_messages = self.extract_voice_messages(message_result)
        for voice_msg in voice_messages:
            self.process_voice_message(voice_msg)
        
        logger.info(f"Processed {processed_count} images from {chat_name}")
        return processed_count
    
    def extract_voice_messages(self, message_result):
        """
        Extract voice messages from message result
        
        Args:
            message_result (dict): Result from get_next_new_message
            
        Returns:
            list: List of voice messages with text content
        """
        if not message_result.get("success") or not message_result.get("has_message"):
            return []
        
        voice_messages = []
        for msg in message_result.get("messages", []):
            if (msg.get("type") == "voice" and 
                "Voice" in msg.get("class", "") and
                msg.get("voice_convert_success") == True and
                msg.get("voice_to_text")):
                
                voice_messages.append({
                    "chat_name": msg.get("chat_name"),
                    "voice_text": msg.get("voice_to_text"),
                    "message_id": msg.get("id"),
                    "raw_message": msg
                })
                logger.info(f"Found voice message: {msg.get('voice_to_text')[:50]}...")
        
        return voice_messages
    
    def process_voice_message(self, voice_msg):
        """
        Process a voice message
        
        Args:
            voice_msg (dict): Voice message data
        """
        try:
            logger.info(f"Processing voice message from: {voice_msg['chat_name']}")
            logger.info(f"Voice content: {voice_msg['voice_text']}")
            
            # Here you can add logic to handle voice message content
            # For example, check for specific commands or keywords
            
            # Example: If voice contains "作业" keyword, trigger homework processing
            if "作业" in voice_msg['voice_text']:
                logger.info("Detected homework-related voice message")
                # Add your specific logic here
            
        except Exception as e:
            logger.error(f"Error processing voice message: {str(e)}")
    
    def main_loop(self, check_interval=3):
        """
        Main processing loop with synchronous processing
        
        Args:
            check_interval (int): Interval between checks in seconds
        """
        self.running = True
        logger.info("Starting main loop with synchronous processing...")
        logger.info(f"Download path: {self.download_path}")
        logger.info(f"Check interval: {check_interval}s")
        
        total_processed = 0
        
        try:
            while self.running:
                # Get new messages
                message_result = self.wxauto.get_next_new_message()
                
                # Process the messages synchronously
                processed_count = self.process_message_batch(message_result)
                total_processed += processed_count
                
                # Wait before next check
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("Main loop interrupted by user")
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
        finally:
            self.running = False
            logger.info(f"Main loop stopped. Total images processed: {total_processed}")
    
    def stop(self):
        """Stop the main loop"""
        self.running = False
        logger.info("Stopping main loop...")


def main():
    """Main function"""
    print("Starting Main Loop Processor with Synchronous Processing...")
    
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