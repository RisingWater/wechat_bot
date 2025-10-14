# homework.py
import logging
import json
from baidu_ocr import BaiduOCR
from deepseek import DeepSeekAPI

logger = logging.getLogger(__name__)

class HomeworkProcessor:
    def __init__(self, env_file=".env"):
        self.ocr = BaiduOCR(env_file)
        self.deepseek = DeepSeekAPI(env_file)
    
    def _generate_ocr_prompt(self, ocr_results):
        """
        Generate prompt for DeepSeek to organize OCR results
        
        Args:
            ocr_results (list): List of OCR text results
            
        Returns:
            str: Formatted prompt for DeepSeek
        """
        # Extract text from OCR results
        ocr_texts = [item['text'] for item in ocr_results]
        ocr_content = "\n".join([f"{i+1}. {text}" for i, text in enumerate(ocr_texts)])
        
        prompt = f"""
请分析并整理以下从作业图片中识别出的文字内容。
这些内容可能有分栏布局（比如左边是A班，右边是B班）或其他排版方式。

OCR识别结果：
{ocr_content}

请按照以下要求处理：
1. 分析文字之间的空间关系和布局结构
2. 识别是否存在不同班级或部分的分栏
3. 根据位置信息将内容按逻辑整理
4. 输出清晰、结构良好的文本，保持原意
5. 如果检测到多个班级或部分，请明确分开

重要要求：
- 请不要使用Markdown格式
- 具体格式可以参考下面例子
十月十日
语文:
1.阳光课堂练习P43-46.
2.准备小测
数学:
1.卷子一张:P67-P68.
英语: 
A班
1.红皮P24课时五.
2.红皮P29.看图短语填空 
B班
1.同上1.2.
2.准备小测strict-northern
历史:
顶尖课课练P22.
物理
1、校本练习一张

请只输出整理后的文本内容，不要添加额外的解释说明。如果识别结果与作业无关请直接输出"这不是作业"
"""
        return prompt
    
    def organize_ocr_with_deepseek(self, ocr_results):
        """
        Use DeepSeek to organize OCR results
        
        Args:
            ocr_results (list): List of OCR text results
            
        Returns:
            str: Organized text content, or None if failed
        """
        try:
            # Generate prompt
            prompt = self._generate_ocr_prompt(ocr_results)
            
            # Send to DeepSeek
            organized_text = self.deepseek.ask_question(prompt)
            
            if organized_text:
                logger.info("Successfully organized OCR results with DeepSeek")
                return organized_text
            else:
                logger.error("Failed to organize OCR results with DeepSeek")
                return None
                
        except Exception as e:
            logger.error(f"Error organizing OCR with DeepSeek: {str(e)}")
            return None
    
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
                
                # Use DeepSeek to organize the results
                organized_text = self.organize_ocr_with_deepseek(ocr_result['results'])
                
                return {
                    "success": True,
                    "image_file": image_path,
                    "chat_name": chat_name,
                    "ocr_text": all_text,
                    "organized_text": organized_text,
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
        organized_text = ocr_result.get('organized_text')
        
        logger.info(f"OCR result for {ocr_result['image_file']}:")
        logger.info(f"Chat: {chat_name}")
        logger.info(f"Raw OCR text: {ocr_text}")
        
        if organized_text:
            logger.info(f"Organized text: {organized_text}")
        
        # Send response back to user
        if wxauto_client and chat_name:
            if organized_text:
                # Send organized text
                response_msg = f"{organized_text}"
            else:
                # Send raw OCR text
                response_msg = f"整理作业失败"
            
            wxauto_client.send_text_message(
                who=chat_name,
                msg=response_msg
            )
        
        # TODO: Add more homework-specific logic here
        # For example:
        # - Save to database
        # - Analyze homework content
        # - Generate reports
        # - Integrate with other services