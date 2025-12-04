# process_router.py
import logging
import json
import os

from pathlib import Path
from typing import List, Dict, Any
from env import EnvConfig
from config import ConfigManager

logger = logging.getLogger(__name__)

class ProcessRouter:
    def __init__(self, env_file=".env"):
        self._config = EnvConfig(env_file)
        self._config_manager = ConfigManager(env_file)
        self.processors = {}
        logger.info("Initializing process router...")
  
    def register_processor(self, name: str, processor_instance):
        """注册处理器"""
        self.processors[name] = processor_instance
        self._config_manager.update_processor(name, processor_instance.description())

    def get_processors_for_chat(self, chat_name: str) -> List[Any]:
        """
        根据聊天名称和消息内容获取对应的处理器列表
        """
        processor_names = []
        processor_names = self._config_manager.find_processor(chat_name)
        logger.info(f"精确匹配聊天名称 '{chat_name}' -> {processor_names}")
        
        # 去重并返回处理器实例
        valid_processors = []
        for name in processor_names:
            if name in self.processors:
                valid_processors.append(self.processors[name])
            else:
                logger.warning(f"处理器未注册: {name}")
        
        if not valid_processors:
            logger.info(f"没有找到匹配的处理器 for chat: {chat_name}")
        
        # 按照 priority 排序，大的在前面
        valid_processors.sort(key=lambda processor: processor.priority(), reverse=True)

        return valid_processors
    
    def extract_messages_by_type(self, message_batch: Dict[str, Any]) -> List:
        """
        从消息批次中按类型提取消息
        """
        msglist = []

        if not message_batch.get("success") or not message_batch.get("has_message"):
            return msglist
        
        messages = message_batch.get("messages", [])
        
        for msg in messages:
            if msg.get("attr") == "self":
                logger.info(f"跳过自己发送的消息: {msg.get('content', '')[:50]}...")
                continue

            logger.info(f"开始处理消息\n%s", json.dumps(msg, ensure_ascii=False,  indent=2))

            msg_type = msg.get("type", "")
            
            if msg_type == "image" and msg.get("download_success") == True and msg.get("file_id") and msg.get("file_info"):
                msglist.append({
                    "msg_type" : "image",
                    "chat_type": msg.get("chat_type"),
                    "chat_name": msg.get("chat_name"),
                    "file_id": msg.get("file_id"),
                    "file_name": msg.get("file_info").get("filename"),
                    "message_id": msg.get("id"),
                    "content": msg.get("content", ""),
                    "raw_message": msg
                })
            elif msg_type == "file" and msg.get("download_success") == True and msg.get("file_id") and msg.get("file_info"):
                msglist.append({
                    "msg_type" : "file",
                    "chat_type": msg.get("chat_type"),
                    "chat_name": msg.get("chat_name"),
                    "file_id": msg.get("file_id"),
                    "file_name": msg.get("file_info").get("filename"),
                    "message_id": msg.get("id"),
                    "content": msg.get("content", ""),
                    "raw_message": msg
                })
                
            elif msg_type == "voice" and msg.get("voice_convert_success") == True:
                msglist.append({
                    "msg_type" : "voice",
                    "chat_type": msg.get("chat_type"),
                    "chat_name": msg.get("chat_name"),
                    "voice_text": msg.get("voice_to_text", ""),
                    "message_id": msg.get("id"),
                    "content": msg.get("content", ""),
                    "raw_message": msg
                })
                
            elif msg_type == "text":
                msglist.append({
                    "msg_type" : "text",
                    "chat_type": msg.get("chat_type"),
                    "chat_name": msg.get("chat_name"),
                    "text_content": msg.get("content", ""),
                    "message_id": msg.get("id"),
                    "raw_message": msg
                })

            elif msg_type == "link" and msg.get("get_url_success") == True:
                msglist.append({
                    "msg_type" : "link",
                    "chat_type": msg.get("chat_type"),
                    "chat_name": msg.get("chat_name"),
                    "text_content": msg.get("content", ""),
                    "url": msg.get("url"),
                    "message_id": msg.get("id"),
                    "raw_message": msg
                })
        
        return msglist
    
    def route_message_batch(self, message_batch: Dict[str, Any], wxauto_client) -> Dict[str, Any]:
        """
        路由消息批次到相应的处理器
        """
        if not message_batch.get("success") or not message_batch.get("has_message"):
            return {"processed": 0, "errors": 0, "processors_used": []}
        
        chat_name = message_batch.get("chat_name")
        logger.info(f"开始处理来自 '{chat_name}' 的消息")
        
        # 提取消息并按类型分类
        message_list = self.extract_messages_by_type(message_batch)
                
        # 处理图片消息
        for msg in message_list:
            #logger.info(f"开始处理消息\n%s", json.dumps(msg["raw_message"], ensure_ascii=False, indent=2))
            processors = self.get_processors_for_chat(chat_name)
            for processor in processors:
                if hasattr(processor, 'process_image') and msg.get('msg_type') == 'image':
                    try:
                        result = processor.process_image(msg, wxauto_client)
                        if result:
                            logger.info(f"{processor.__class__.__name__} 成功处理图片: {msg['text_content']}")
                            break
                    except Exception as e:
                        logger.error(f"处理器 {processor.__class__.__name__} 处理图片错误: {str(e)}")
        
                if hasattr(processor, 'process_voice') and msg.get('msg_type') == 'voice':
                    try:
                        result = processor.process_voice(msg, wxauto_client)
                        if result:
                            logger.info(f"{processor.__class__.__name__} 成功处理语音: {msg['voice_text'][:50]}...")
                            break
                    except Exception as e:
                        logger.error(f"处理器 {processor.__class__.__name__} 处理语音错误: {str(e)}")
        
                if hasattr(processor, 'process_text') and msg.get('msg_type') == 'text':
                    try:
                        result = processor.process_text(msg, wxauto_client)
                        if result:
                            logger.info(f"{processor.__class__.__name__} 成功处理文本: {msg['text_content'][:50]}...")
                            break
                    except Exception as e:
                        logger.error(f"处理器 {processor.__class__.__name__} 处理文本错误: {str(e)}")

                if hasattr(processor, 'process_file') and msg.get('msg_type') == 'file':
                    try:
                        result = processor.process_file(msg, wxauto_client)
                        if result:
                            logger.info(f"{processor.__class__.__name__} 成功处理文件: {msg['text_content']}")
                            break   
                    except Exception as e:
                        logger.error(f"处理器 {processor.__class__.__name__} 处理文件错误: {str(e)}")   
                
                if hasattr(processor, 'process_url') and msg.get('msg_type') == 'link':
                    try:
                        result = processor.process_url(msg, wxauto_client)
                        if result:
                            logger.info(f"{processor.__class__.__name__} 成功链接: {msg['url']}")
                            break   
                    except Exception as e:
                        logger.error(f"处理器 {processor.__class__.__name__} 处理链接错误: {str(e)}")   
        
        # 清理文件
        for msg in message_list:
            file_id = msg.get('file_id')
            if file_id:
                wxauto_client.delete_file(file_id)