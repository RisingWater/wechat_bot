# homework.py
import logging
import json
import os
import shutil
import tempfile
from webapi.baidu_ocr import BaiduOCR
from webapi.deepseek import DeepSeekAPI

logger = logging.getLogger(__name__)

class HomeworkProcessor:
    def __init__(self, env_file=".env"):
        self._ocr = BaiduOCR(env_file)
        self._deepseek = DeepSeekAPI(env_file)
        self.processor_name = "homework_processor"
        logger.info(f"HomeworkProcessor initialized")
    
    def description(self) -> str:
        return "作业OCR处理器"
    
    def priority(self) -> int:
        return 10

    def process_image(self, image_msg, wxauto_client):
        """
        处理图片消息 - 实现BaseProcessor接口
        
        Args:
            image_msg (dict): 图片消息数据
            wxauto_client: wxauto客户端实例
            
        Returns:
            bool: 处理成功返回True，失败返回False
        """
        try:
            chat_name = image_msg.get("chat_name")
            file_name = image_msg.get("file_name")
            file_id = image_msg.get("file_id")

            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, file_name)

            download_ret = wxauto_client.download_file(file_id, file_path)
            
            #{"success": False, "error": error_msg}
            if not download_ret.get('success'):
                logger.error(f"Download failed for {file_path}: {download_ret.get('error')}")
                self._send_error_response(wxauto_client, chat_name, f"图片下载失败: {download_ret.get('error', '未知错误')}")
                return False
            
            logger.info(f"HomeworkProcessor processing image from {chat_name}: {file_path}")
            
            # 使用百度OCR处理图片
            ocr_result = self._ocr.recognize_handwriting(file_path)
            
            if not ocr_result.get('success'):
                logger.error(f"OCR failed for {file_path}: {ocr_result.get('error')}")
                self._send_error_response(wxauto_client, chat_name, f"图片识别失败: {ocr_result.get('error', '未知错误')}")
                return False
            
            logger.info(f"OCR successful for {file_path}, found {len(ocr_result['results'])} text items")
            
            # 提取所有文本
            all_text = " ".join([item['text'] for item in ocr_result['results']])
            logger.info(f"OCR text preview: {all_text[:100]}...")
            
            # 使用DeepSeek整理结果
            organized_text = self._organize_ocr_with_deepseek(ocr_result['results'])
            
            if organized_text:
                # 发送整理后的文本给用户
                response_msg = f"作业内容整理：\n\n{organized_text}"
                wxauto_client.send_text_message(who=chat_name, msg=response_msg)
                logger.info(f"Successfully processed homework image and sent response to {chat_name}")
                
                return True
            else:
                error_msg = "作业内容整理失败，请重试或联系管理员"
                self._send_error_response(wxauto_client, chat_name, error_msg)
                return False
                
        except Exception as e:
            logger.error(f"Error processing homework image: {str(e)}")
            self._send_error_response(wxauto_client, image_msg.get("chat_name"), f"处理图片时发生错误: {str(e)}")
            return False

        finally:
            # 确保清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")

            
    def _organize_ocr_with_deepseek(self, ocr_results):
        """
        使用DeepSeek整理OCR结果
        
        Args:
            ocr_results (list): OCR结果列表
            
        Returns:
            str: 整理后的文本内容
        """
        try:
            prompt = self._generate_ocr_prompt(ocr_results)
            organized_text = self._deepseek.ask_question(prompt)
            
            logger.info("Successfully organized OCR results with DeepSeek")
            return organized_text
                
        except Exception as e:
            logger.error(f"Error organizing OCR with DeepSeek: {str(e)}")
            return None
    
    def _generate_ocr_prompt(self, ocr_results):
        """
        生成DeepSeek提示词
        
        Args:
            ocr_results (list): OCR结果列表
            
        Returns:
            str: 格式化后的提示词
        """
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
      
    def _send_error_response(self, wxauto_client, chat_name, error_message):
        """
        发送错误响应
        
        Args:
            wxauto_client: wxauto客户端实例
            chat_name (str): 聊天名称
            error_message (str): 错误消息
        """
        if wxauto_client and chat_name:
            try:
                wxauto_client.send_text_message(who=chat_name, msg=error_message)
            except Exception as e:
                logger.error(f"Failed to send error response: {str(e)}")
    