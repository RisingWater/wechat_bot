# process_router.py
import logging
import json
from pathlib import Path
from typing import List, Dict, Any
from env import EnvConfig

logger = logging.getLogger(__name__)

class ProcessRouter:
    def __init__(self, config_file: str = "processor_config.json", env_file=".env"):
        self._config = EnvConfig(env_file)
        self.processors = {}
        self.chat_name_processor_config = {}
        self.cmd_list = []
        self.download_path = self._get_download_path()
        
        # 加载配置文件
        self._load_config(config_file)
        
    def _load_config(self, config_file: str):
        """从JSON文件加载配置"""
        config_path = Path(config_file)
        
        if not config_path.exists():
            logger.warning(f"配置文件 {config_file} 不存在，使用默认配置")
            self._set_default_config()
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.chat_name_processor_config = config.get("chat_name_processor_config", {})
            self.cmd_list = config.get("cmd_list", [])
            
            logger.info(f"成功加载配置文件: {config_file}")
            logger.info(f"聊天配置: {list(self.chat_name_processor_config.keys())}")
            logger.info(f"命令列表: {self.cmd_list}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}，使用默认配置")
            self._set_default_config()
    
    def _set_default_config(self):
        """设置默认配置"""
        self.chat_name_processor_config = {
            "作业识别": ["homework_processor"],
            "文件打印": ["print_processor"],
            "王旭": ["cmd_processor", "chat_processor"],
            "心颖": ["chat_processor"]
        }
        self.cmd_list = [
            "打开电视",
            "关闭电视"
        ]
        logger.info("使用默认配置")
    
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

    def register_processor(self, name: str, processor_instance):
        """注册处理器"""
        self.processors[name] = processor_instance
        logger.info(f"Registered processor: {name}")
    
    def get_processors_for_chat(self, chat_name: str, message_content: str = "") -> List[Any]:
        """
        根据聊天名称和消息内容获取对应的处理器列表
        """
        processor_names = []
        
        # 1. 精确匹配聊天名称
        if chat_name in self.chat_name_processor_config:
            processor_names = self.chat_name_processor_config[chat_name]
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
        
        return valid_processors
    
    def extract_messages_by_type(self, message_batch: Dict[str, Any]) -> Dict[str, List]:
        """
        从消息批次中按类型提取消息
        """
        if not message_batch.get("success") or not message_batch.get("has_message"):
            return {"images": [], "voices": [], "texts": []}
        
        messages = message_batch.get("messages", [])
        
        images = []
        voices = []
        texts = []
        
        for msg in messages:
            if msg.get("attr") == "self":
                logger.info(f"跳过自己发送的消息: {msg.get('content', '')[:50]}...")
                continue

            msg_type = msg.get("type", "")
            
            if msg_type == "image" and msg.get("download_success") == True and msg.get("file_name"):
                images.append({
                    "chat_name": msg.get("chat_name"),
                    "file_name": msg.get("file_name"),
                    "file_path": self.download_path / msg.get("file_name"),
                    "message_id": msg.get("id"),
                    "content": msg.get("content", ""),
                    "raw_message": msg
                })
                
            elif msg_type == "voice" and msg.get("voice_convert_success") == True:
                voices.append({
                    "chat_name": msg.get("chat_name"),
                    "voice_text": msg.get("voice_to_text", ""),
                    "message_id": msg.get("id"),
                    "content": msg.get("content", ""),
                    "raw_message": msg
                })
                
            elif msg_type == "text":
                texts.append({
                    "chat_name": msg.get("chat_name"),
                    "text_content": msg.get("content", ""),
                    "message_id": msg.get("id"),
                    "raw_message": msg
                })
        
        return {
            "images": images,
            "voices": voices, 
            "texts": texts
        }
    
    def route_message_batch(self, message_batch: Dict[str, Any], wxauto_client) -> Dict[str, Any]:
        """
        路由消息批次到相应的处理器
        """
        if not message_batch.get("success") or not message_batch.get("has_message"):
            return {"processed": 0, "errors": 0, "processors_used": []}
        
        chat_name = message_batch.get("chat_name")
        logger.info(f"开始处理来自 '{chat_name}' 的消息")
        
        # 提取消息并按类型分类
        messages_by_type = self.extract_messages_by_type(message_batch)
        
        # 为每条消息单独选择处理器（因为同批次可能有命令消息和非命令消息）
        total_processed = 0
        total_errors = 0
        used_processors = set()
        
        # 处理图片消息
        for img_msg in messages_by_type["images"]:
            processors = self.get_processors_for_chat(chat_name)
            for processor in processors:
                if hasattr(processor, 'process_image'):
                    try:
                        result = processor.process_image(img_msg, wxauto_client)
                        if result:
                            total_processed += 1
                            used_processors.add(processor.__class__.__name__)
                            logger.info(f"{processor.__class__.__name__} 成功处理图片: {img_msg['file_name']}")
                            break
                        else:
                            total_errors += 1
                    except Exception as e:
                        logger.error(f"处理器 {processor.__class__.__name__} 处理图片错误: {str(e)}")
                        total_errors += 1
        
        # 处理语音消息
        for voice_msg in messages_by_type["voices"]:
            # 使用语音内容进行命令检测
            processors = self.get_processors_for_chat(chat_name, voice_msg["voice_text"])
            for processor in processors:
                if hasattr(processor, 'process_voice'):
                    try:
                        result = processor.process_voice(voice_msg, wxauto_client)
                        if result:
                            total_processed += 1
                            used_processors.add(processor.__class__.__name__)
                            logger.info(f"{processor.__class__.__name__} 成功处理语音: {voice_msg['voice_text'][:50]}...")
                            break
                        else:
                            total_errors += 1
                    except Exception as e:
                        logger.error(f"处理器 {processor.__class__.__name__} 处理语音错误: {str(e)}")
                        total_errors += 1
        
        # 处理文本消息
        for text_msg in messages_by_type["texts"]:
            # 使用文本内容进行命令检测
            processors = self.get_processors_for_chat(chat_name, text_msg["text_content"])
            for processor in processors:
                if hasattr(processor, 'process_text'):
                    try:
                        result = processor.process_text(text_msg, wxauto_client)
                        if result:
                            total_processed += 1
                            used_processors.add(processor.__class__.__name__)
                            logger.info(f"{processor.__class__.__name__} 成功处理文本: {text_msg['text_content'][:50]}...")
                            break
                        else:
                            total_errors += 1
                    except Exception as e:
                        logger.error(f"处理器 {processor.__class__.__name__} 处理文本错误: {str(e)}")
                        total_errors += 1
        
        logger.info(f"处理完成: 成功 {total_processed}, 失败 {total_errors}")
        return {
            "processed": total_processed,
            "errors": total_errors,
            "processors_used": list(used_processors)
        }