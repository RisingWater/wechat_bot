# chat_processor.py
import logging
import time
from datetime import datetime, timedelta
from webapi.deepseek import DeepSeekAPI

logger = logging.getLogger(__name__)

class ChatProcessor:
    def __init__(self, env_file=".env"):
        self._deepseek = DeepSeekAPI(env_file)
        self.processor_name = "chat_processor"
        
        # 会话存储：{chat_name: {"messages": [], "last_active": timestamp}}
        self.sessions = {}
        
        # 会话超时时间（10分钟）
        self.session_timeout = 600  # 10分钟
        
        logger.info("ChatProcessor initialized with session memory")
    
    def process_voice(self, voice_msg, wxauto_client):
        """
        处理语音消息
        
        Args:
            voice_msg (dict): 语音消息数据
            wxauto_client: wxauto客户端实例
            
        Returns:
            bool: 处理成功返回True，失败返回False
        """
        try:
            chat_name = voice_msg.get("chat_name")
            voice_text = voice_msg.get("voice_text")
            
            # 清理过期会话
            self._cleanup_expired_sessions()
            
            if not voice_text or not voice_text.strip():
                response_msg = "抱歉，我没有听清楚您的语音内容，请重试或发送文字消息。"
                wxauto_client.send_text_message(who=chat_name, msg=response_msg)
                return False
            
            # 将语音文本作为用户消息处理
            return self._process_user_message(chat_name, voice_text, wxauto_client)
            
        except Exception as e:
            logger.error(f"Error processing chat voice: {str(e)}")
            return False
    
    def process_text(self, text_msg, wxauto_client):
        """
        处理文本消息
        
        Args:
            text_msg (dict): 文本消息数据
            wxauto_client: wxauto客户端实例
            
        Returns:
            bool: 处理成功返回True，失败返回False
        """
        try:
            chat_name = text_msg.get("chat_name")
            text_content = text_msg.get("text_content")
            
            # 清理过期会话
            self._cleanup_expired_sessions()
            
            if not text_content or not text_content.strip():
                response_msg = "您好！我是您的AI助手，有什么可以帮您的吗？"
                wxauto_client.send_text_message(who=chat_name, msg=response_msg)
                return True
            
            # 处理用户消息
            return self._process_user_message(chat_name, text_content, wxauto_client)
            
        except Exception as e:
            logger.error(f"Error processing chat text: {str(e)}")
            return False
    
    def _process_user_message(self, chat_name, user_message, wxauto_client):
        """
        处理用户消息，维护会话记忆
        
        Args:
            chat_name (str): 聊天名称
            user_message (str): 用户消息
            wxauto_client: wxauto客户端实例
            
        Returns:
            bool: 处理成功返回True，失败返回False
        """
        try:
            logger.info(f"Processing chat message from {chat_name}: {user_message[:50]}...")
            
            # 检查会话是否存在或过期
            current_time = time.time()
            if chat_name in self.sessions:
                session = self.sessions[chat_name]
                time_diff = current_time - session["last_active"]
                
                # 如果超过10分钟，清除会话历史
                if time_diff > self.session_timeout:
                    logger.info(f"Session expired for {chat_name}, clearing history")
                    self.sessions[chat_name] = {
                        "messages": [],
                        "last_active": current_time
                    }
                else:
                    # 更新最后活跃时间
                    session["last_active"] = current_time
            else:
                # 创建新会话
                self.sessions[chat_name] = {
                    "messages": [],
                    "last_active": current_time
                }
                logger.info(f"Created new session for {chat_name}")
            
            # 获取当前会话
            session = self.sessions[chat_name]
            
            # 添加用户消息到会话历史
            session["messages"].append({
                "role": "user",
                "content": user_message,
                "timestamp": current_time
            })
            
            # 构建DeepSeek消息格式
            deepseek_messages = self._build_deepseek_messages(session["messages"])
            
            # 调用DeepSeek API
            response = self._deepseek.ask_question(deepseek_messages)
            
            if response:
                # 添加AI回复到会话历史
                session["messages"].append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": current_time
                })
                                
                # 发送回复给用户
                wxauto_client.send_text_message(who=chat_name, msg=response)
                logger.info(f"Successfully sent chat response to {chat_name}")
                return True
            else:
                error_msg = "抱歉，我现在无法回复您，请稍后重试。"
                wxauto_client.send_text_message(who=chat_name, msg=error_msg)
                logger.error(f"DeepSeek API failed for {chat_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing user message for {chat_name}: {str(e)}")
            error_msg = "处理消息时出现错误，请稍后重试。"
            wxauto_client.send_text_message(who=chat_name, msg=error_msg)
            return False
    
    def _build_deepseek_messages(self, session_messages):
        """
        构建DeepSeek API需要的消息格式
        
        Args:
            session_messages (list): 会话消息历史
            
        Returns:
            str: 格式化后的消息内容
        """
        # 如果有历史消息，构建带上下文的对话
        if len(session_messages) > 1:
            # 将整个对话历史构建成一个连贯的文本
            conversation = []
            for msg in session_messages:
                role = "用户" if msg["role"] == "user" else "助手"
                conversation.append(f"{role}: {msg['content']}")
            
            # 构建最终的提示词
            prompt = """请根据以下对话历史继续回答用户的问题，保持对话的连贯性。

    对话历史：
    {}

    请用简洁明了的语言回答，确保回复内容在200字以内。""".format("\n\n".join(conversation))
            return prompt
        else:
            # 只有当前用户消息，添加明确的字数要求
            user_message = session_messages[0]["content"]
            prompt = f"{user_message}\n\n请用简洁的语言回答这个问题，确保回复内容不超过200字。"
            return prompt
    
    def _cleanup_expired_sessions(self):
        """
        清理过期的会话
        """
        current_time = time.time()
        expired_sessions = []
        
        for chat_name, session in self.sessions.items():
            time_diff = current_time - session["last_active"]
            if time_diff > self.session_timeout:
                expired_sessions.append(chat_name)
        
        for chat_name in expired_sessions:
            del self.sessions[chat_name]
            logger.info(f"Cleaned up expired session for {chat_name}")
    
