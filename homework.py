# homework.py
import logging
from baidu_ocr import BaiduOCR

logger = logging.getLogger(__name__)

class HomeworkProcessor:
    def __init__(self, env_file=".env"):
        self.ocr = BaiduOCR(env_file)
    
    def process_image_with_ocr(self, image_path, chat_name=""):
        """
        Process image with OCR and return results
        
        Args:
            image_path (str): Path to the image file
            chat_name (str): Name of the chat/sender
            
        Returns:
            dict: OCR processing result
        """
        try:
            logger.info(f"Processing image with OCR: {image_path}")
            
            # Use Baidu OCR to process image
            ocr_result = self.ocr.recognize_handwriting(image_path)
            
            if ocr_result.get('success'):
                logger.info(f"OCR successful for {image_path}, found {len(ocr_result['results'])} text items")
                
                # Extract all text
                all_text = " ".join([item['text'] for item in ocr_result['results']])
                logger.info(f"OCR text preview: {all_text[:100]}...")
                
                return {
                    "success": True,
                    "image_file": image_path,
                    "chat_name": chat_name,
                    "ocr_text": all_text,
                    "detailed_results": ocr_result['results'],
                    "raw_ocr_result": ocr_result
                }
            else:
                logger.error(f"OCR failed for {image_path}: {ocr_result.get('error')}")
                return {
                    "success": False,
                    "image_file": image_path,
                    "chat_name": chat_name,
                    "error": ocr_result.get('error'),
                    "raw_ocr_result": ocr_result
                }
                
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            return {
                "success": False,
                "image_file": image_path,
                "chat_name": chat_name,
                "error": str(e)
            }
    
    def handle_ocr_result(self, ocr_result, wxauto_client=None):
        """
        Handle OCR result - custom logic for homework processing
        
        Args:
            ocr_result (dict): OCR processing result
            wxauto_client: WXAuto client instance for sending responses
        """
        if not ocr_result['success']:
            logger.error(f"OCR processing failed: {ocr_result.get('error')}")
            
            # Optionally send error message back to user
            if wxauto_client and ocr_result.get('chat_name'):
                error_msg = f"图片识别失败: {ocr_result.get('error', '未知错误')}"
                wxauto_client.send_text_message(
                    who=ocr_result['chat_name'],
                    msg=error_msg
                )
            return
        
        # Custom logic for homework processing
        chat_name = ocr_result['chat_name']
        ocr_text = ocr_result['ocr_text']
        
        logger.info(f"OCR result for {ocr_result['image_file']}:")
        logger.info(f"Chat: {chat_name}")
        logger.info(f"Text: {ocr_text}")
        
        # Example: Send OCR result back to the sender
        if wxauto_client and chat_name:
            # You can customize the response message here
            response_msg = f"图像识别结果:\n{ocr_text}"
            wxauto_client.send_text_message(
                who=chat_name,
                msg=response_msg
            )
        
        