import requests
import threading
import time
import logging
from typing import Optional, Dict, Any

class AudioPlayer:
    def __init__(self, base_url: str = "http://192.168.1.180:6018"):
        """
        初始化 AudioPlayer
        
        Args:
            base_url: TTS 服务的基础 URL
        """
        self.base_url = base_url.rstrip('/')
        self.sessions = {}  # 存储会话状态
        self._stop_monitoring = False
        self.monitor_thread = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def speak(self, text: str, voice: str = "zh-CN-XiaoxiaoNeural") -> Optional[str]:
        """
        发送 TTS 请求并开始监控会话状态
        
        Args:
            text: 要合成的文本
            voice: 语音名称
            rate: 语速
            volume: 音量
            volume_level: 音量级别
            stream: 是否流式
            
        Returns:
            session_id: 会话ID，如果失败则返回None
        """
        url = f"{self.base_url}/api/tts/speak"
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        data = {
            "text": text,
            "voice": voice,
            "volume": 1,
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            session_id = result.get("session_id")
            return session_id
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求异常: {e}")
            return None
        except Exception as e:
            self.logger.error(f"未知错误: {e}")
            return None


# 使用示例
if __name__ == "__main__":
    # 创建 AudioPlayer 实例
    player = AudioPlayer("http://192.168.1.180:6018")
    
    # 发送 TTS 请求
    session_id = player.speak("王旭，欢迎回家", volume_level=0.8)
    
    if session_id:
        print(f"语音生成已启动，会话ID: {session_id}")
        
        # 等待一段时间查看状态
        time.sleep(5)
        
        # 获取当前会话状态
        status = player.get_session_status(session_id)
        print(f"当前会话状态: {status}")
        
        # 获取所有活跃会话
        all_sessions = player.get_all_sessions()
        print(f"活跃会话: {all_sessions}")
        
        # 等待更长时间以确保完成
        time.sleep(10)
        
        # 停止监控
        player.stop_monitoring()
    else:
        print("语音生成请求失败")