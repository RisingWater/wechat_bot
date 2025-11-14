# homework.py
import logging
import json
import uuid
import os
import shutil
import tempfile
import threading
import time
from utils.fixed_web_converter import FixedWebConverter

logger = logging.getLogger(__name__)

class UrlSaveProcessor:
    def __init__(self, env_file=".env"):
        self.processor_name = "urlsave_processor"
        logger.info(f"UrlSaveProcessor initialized")
    
    def description(self) -> str:
        return "公众号链接保存处理器"  
        
    def process_url(self, link_msg, wxauto_client):
        """
        处理文件消息 - 实现BaseProcessor接口
        
        Args:
            link_msg (dict): 链接消息数据
            wxauto_client: wxauto客户端实例
            
        Returns:
            bool: 处理成功返回True，失败返回False
        """
        try:
            chat_name = link_msg.get("chat_name")
            url = link_msg.get("url")

            temp_dir = tempfile.mkdtemp()
            docx_name = os.path.join(temp_dir, "output.docx")

            converter = FixedWebConverter()

            converter.convert_url_to_docx(url, docx_name)

            if os.path.exists(docx_name):
                wxauto_client.send_file_message(who=chat_name, file_path=docx_name)
            else:
                self._send_error_response(wxauto_client, chat_name, "转化docx文件失败，请检查链接")
                            
        except Exception as e:
            logger.error(f"Error processing printer file: {str(e)}")
            self._send_error_response(wxauto_client, chat_name, f"处理文件时发生错误: {str(e)}")
            return False

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
  