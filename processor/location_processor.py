# cmd_processor.py
import logging
import uuid
import os
from webapi.deepseek import DeepSeekAPI
from webapi.amap import AmapAPI
from device.qb_location import QBLocation

logger = logging.getLogger(__name__)

class LocationProcessor:
    def __init__(self, env_file=".env"):
        self._deepseek = DeepSeekAPI(env_file)
        self._qb_location = QBLocation()
        self._amap_api = AmapAPI(env_file)
        self.processor_name = "location_processor"
        
        logger.info("LocationProcessor initialized with DeepSeek command recognition")
    
    def process_text(self, text_msg, wxauto_client):
        """
        处理文本消息 - 使用DeepSeek识别文本中的命令意图
        """
        try:
            chat_name = text_msg.get("chat_name")
            text_content = text_msg.get("text_content")
            
            if not text_content or not text_content.strip():
                logger.info(f"Empty text message from {chat_name}, skipping")
                return False
            
            logger.info(f"LocationProcessor processing text from {chat_name}: {text_content[:50]}...")
            
            # 检查是否包含"@呼噜一号"，如果有则去掉
            processed_content = text_content
            if not "@呼噜一号" in text_content:
                logger.info(f"text message from {chat_name}, not @bot skipping")
                return False
            
            processed_content = text_content.replace("@呼噜一号", "").strip()
            logger.info(f"Removed '@呼噜一号' from message, processed content: {processed_content}")
        
            # 使用处理后的内容判断命令意图
            is_command = self._recognize_command_intent(processed_content)

            if is_command:
                self._qb_location(wxauto_client)
                return True
                            
        except Exception as e:
            logger.error(f"Error processing command text: {str(e)}")
            return False
    def _recognize_command_intent(self, user_input):
        """
        使用DeepSeek识别用户的命令意图
        
        Args:
            user_input (str): 用户输入的文本
            
        Returns:
            bool: 如果是询问位置相关的命令返回True，否则返回False
        """

        try:
            prompt = f"""请分析用户的输入，判断是否是在询问乔宝或者是煜乔或者是王煜乔当前的位置：

用户输入："{user_input}"

请严格按照以下规则判断：
- 如果用户意图匹配上述任一命令，请直接回复："是"
- 如果用户意图不明确或不是位置查询命令，回复："不是"

示例：
用户输入："乔宝位置" -> 回复："是"
用户输入："煜乔到哪里了" -> 回复："是"
用户输入："煜乔当前位置" -> 回复："是"
用户输入："乔宝在哪里" -> 回复："是"
用户输入："今天天气怎么样" -> 回复："不是"
用户输入："打开电视" -> 回复："不是"

请只回复是或不是，不要添加任何其他内容。"""

            response = self._deepseek.ask_question(prompt)
            
            if response:
                response = response.strip()
                logger.info(f"DeepSeek command recognition result: '{response}'")
                
                # 检查响应是否为"是"
                if response == "是":
                    return True
                else:
                    return False
            else:
                logger.error("DeepSeek API returned no response for command recognition")
                return False
                
        except Exception as e:
            logger.error(f"Error in command recognition: {str(e)}")
            return False
        
    def _qb_location(self, chat_name, wxauto_client):
        locations = self._qb_location.get_location()

        if locations.size > 0:
            location = locations[0]
            logger.info(f"Get Qb Location: {location}")

            wxauto_client.send_text_message(chat_name, f"乔宝位置：{location.address}")

            save_path = "/output/wechat_downloads/" + str(uuid.uuid4()) + ".png"

            self._amap_api.get_amap_static_image(
                longitude=location.gcj02_location.longitude,
                latitude=location.gcj02_location.latitude,
                save_path=save_path
                )
            
            wxauto_client.send_file_message(chat_name, save_path)

            os.remove(save_path)
        else:
            self._send_error_response(wxauto_client, chat_name, "没有获取到位置信息")
        
        
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