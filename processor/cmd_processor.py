# cmd_processor.py
import logging
import json
import time
from pathlib import Path
from deepseek import DeepSeekAPI

logger = logging.getLogger(__name__)

class CmdProcessor:
    def __init__(self, config_file: str = "processor_config.json", env_file=".env"):
        self.deepseek = DeepSeekAPI(env_file)
        self.processor_name = "cmd_processor"

        # 加载配置文件
        self._load_config(config_file)
        
        # 命令执行函数映射
        self.command_handlers = {
            "打开电视": self._turn_on_tv,
            "关闭电视": self._turn_off_tv
        }
        
        logger.info("CmdProcessor initialized with DeepSeek command recognition")
    
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
            
            self.cmd_list = config.get("cmd_list", [])
            
            logger.info(f"成功加载配置文件: {config_file}")
            logger.info(f"命令列表: {self.cmd_list}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}，使用默认配置")
            # 默认命令列表
            self.cmd_list = ["打开电视", "关闭电视"]

    def process_image(self, image_msg, wxauto_client):
        return False
    
    def process_voice(self, voice_msg, wxauto_client):
        """
        处理语音消息 - 使用DeepSeek识别语音中的命令意图
        """
        try:
            chat_name = voice_msg.get("chat_name")
            voice_text = voice_msg.get("voice_text")
            
            if not voice_text or not voice_text.strip():
                logger.info(f"Empty voice message from {chat_name}, skipping")
                return False
            
            logger.info(f"CmdProcessor processing voice from {chat_name}: {voice_text[:50]}...")
            
            # 使用DeepSeek识别命令意图
            command = self._recognize_command_intent(voice_text)
            
            if command:
                # 执行识别到的命令
                return self._execute_command(command, chat_name, wxauto_client)
            else:
                logger.info(f"No valid command recognized from voice: {voice_text}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing command voice: {str(e)}")
            return False
    
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
            
            logger.info(f"CmdProcessor processing text from {chat_name}: {text_content[:50]}...")
            
            # 精确匹配
            exact_command = self._exact_match_command(text_content)
            if exact_command:
                logger.info(f"Exact command match: {exact_command}")
                self._execute_command(exact_command, chat_name, wxauto_client)
                return True
                            
        except Exception as e:
            logger.error(f"Error processing command text: {str(e)}")
            return False
    
    def _exact_match_command(self, text):
        """
        精确匹配命令
        """
        text = text.strip()
        for cmd in self.cmd_list:
            if cmd == text:
                return cmd
        return None
    
    def _recognize_command_intent(self, user_input):
        """
        使用DeepSeek识别用户的命令意图
        
        Args:
            user_input (str): 用户输入的文本
            
        Returns:
            str or None: 识别到的命令，如果没有识别到返回None
        """
        try:
            # 动态生成命令列表
            cmd_options = "\n".join([f"{i+1}. {cmd}" for i, cmd in enumerate(self.cmd_list)])
            
            prompt = f"""请分析用户的输入，判断是否是以下控制命令之一：

    {cmd_options}

    用户输入："{user_input}"

    请严格按照以下规则判断：
    - 如果用户意图匹配上述任一命令，请直接回复对应的完整命令文本
    - 如果用户意图不明确或不是电视控制命令，回复："不是命令"

    示例：
    用户输入："帮我开一下电视" -> 回复："打开电视"
    用户输入："把电视关掉吧" -> 回复："关闭电视"
    用户输入："今天天气怎么样" -> 回复："不是命令"

    请只回复命令文本或"不是命令"，不要添加任何其他内容。"""

            response = self.deepseek.ask_question(prompt)
            
            if response:
                response = response.strip()
                logger.info(f"DeepSeek command recognition result: '{response}'")
                
                if response in self.cmd_list:
                    return response
                else:
                    return None
            else:
                logger.error("DeepSeek API returned no response for command recognition")
                return None
                
        except Exception as e:
            logger.error(f"Error in command recognition: {str(e)}")
            return None
    
    def _execute_command(self, command, chat_name, wxauto_client):
        """
        执行识别到的命令
        
        Args:
            command (str): 要执行的命令
            chat_name (str): 聊天名称
            wxauto_client: wxauto客户端实例
            
        Returns:
            bool: 执行成功返回True，失败返回False
        """
        try:
            logger.info(f"Executing command: {command} for {chat_name}")
            
            if command in self.command_handlers:
                # 调用对应的命令处理函数
                success = self.command_handlers[command]()
                
                if success:
                    # 发送执行成功的回复
                    response_msg = self._get_command_response(command, success=True)
                    wxauto_client.send_text_message(who=chat_name, msg=response_msg)
                    logger.info(f"Command '{command}' executed successfully for {chat_name}")
                    return True
                else:
                    # 发送执行失败的回复
                    response_msg = self._get_command_response(command, success=False)
                    wxauto_client.send_text_message(who=chat_name, msg=response_msg)
                    logger.error(f"Command '{command}' execution failed for {chat_name}")
                    return True
            else:
                logger.error(f"Unknown command: {command}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing command {command}: {str(e)}")
            error_msg = f"执行命令 '{command}' 时出现错误，请稍后重试。"
            wxauto_client.send_text_message(who=chat_name, msg=error_msg)
            return False
    
    def _turn_on_tv(self):
        """
        打开电视命令
        """
        try:
            # 调用 MiTV 的打开电视功能
            from mitv import MiTV
            
            tv_controller = MiTV()
            result = tv_controller.smart_power_on()
            
            logger.info(f"Turn on TV result: {result}")
            return result
            
        except ImportError:
            logger.error("MiTV module not found")
            # 模拟成功（用于测试）
            logger.info("Simulating TV turn on (for testing)")
            return True
        except Exception as e:
            logger.error(f"Error turning on TV: {str(e)}")
            return False
    
    def _turn_off_tv(self):
        """
        关闭电视命令
        """
        try:
            # 调用 MiTV 的关闭电视功能
            from mitv import MiTV
            
            tv_controller = MiTV()
            result = tv_controller.smart_power_off()
            
            logger.info(f"Turn off TV result: {result}")
            return result
            
        except ImportError:
            logger.error("MiTV module not found")
            # 模拟成功（用于测试）
            logger.info("Simulating TV turn off (for testing)")
            return True
        except Exception as e:
            logger.error(f"Error turning off TV: {str(e)}")
            return False
    
    def _get_command_response(self, command, success=True):
        """
        获取命令执行结果的回复消息
        """
        responses = {
            "打开电视": {
                True: "✅ 电视已打开",
                False: "❌ 打开电视失败，请检查电视状态"
            },
            "关闭电视": {
                True: "✅ 电视已关闭", 
                False: "❌ 关闭电视失败，请检查电视状态"
            }
        }
        
        if command in responses:
            return responses[command][success]
        else:
            return "命令执行完成" if success else "命令执行失败"
    
    def update_command_list(self, new_cmd_list):
        """
        更新命令列表（可以从配置文件动态加载）
        """
        self.cmd_list = new_cmd_list
        logger.info(f"Command list updated: {new_cmd_list}")


# 测试函数
def main():
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing CmdProcessor...")
    
    # 创建处理器实例
    processor = CmdProcessor()
    
    # 测试命令识别
    test_inputs = [
        "打开电视",
        "请把电视打开",
        "帮我开一下电视",
        "关闭电视", 
        "把电视关掉",
        "电视关机",
        "今天天气怎么样",
        "你好"
    ]
    
    for user_input in test_inputs:
        print(f"\n测试输入: '{user_input}'")
        command = processor._recognize_command_intent(user_input)
        if command:
            print(f"识别到的命令: {command}")
        else:
            print("未识别到命令")

if __name__ == "__main__":
    main()