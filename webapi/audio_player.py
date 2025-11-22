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

    def speak(self, text: str, voice: str = "zh-CN-XiaoxiaoNeural", 
              rate: str = "+0%", volume: str = "+0%", 
              volume_level: float = 0.8, stream: bool = False) -> Optional[str]:
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
            "rate": rate,
            "volume": volume,
            "volume_level": volume_level,
            "stream": stream
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            session_id = result.get("session_id")
            status = result.get("status")
            
            if session_id and status == "generating":
                self.logger.info(f"语音生成中，会话ID: {session_id}")
                self.sessions[session_id] = {
                    "status": status,
                    "text": text,
                    "start_time": time.time()
                }
                
                # 启动监控线程（如果尚未启动）
                self._start_monitoring()
                return session_id
            else:
                self.logger.error(f"请求失败: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求异常: {e}")
            return None
        except Exception as e:
            self.logger.error(f"未知错误: {e}")
            return None

    def _start_monitoring(self):
        """启动监控线程"""
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self._stop_monitoring = False
            self.monitor_thread = threading.Thread(target=self._monitor_sessions, daemon=True)
            self.monitor_thread.start()
            self.logger.info("启动会话监控线程")

    def _monitor_sessions(self):
        """监控所有会话状态的线程函数"""
        while not self._stop_monitoring and self.sessions:
            sessions_to_check = list(self.sessions.keys())
            
            for session_id in sessions_to_check:
                self._check_session_status(session_id)
            
            time.sleep(1)  # 每秒检查一次

    def _check_session_status(self, session_id: str):
        """
        检查单个会话状态
        
        Args:
            session_id: 会话ID
        """
        url = f"{self.base_url}/api/sessions/{session_id}"
        headers = {
            'accept': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            result = response.json()
            
            current_status = result.get("status")
            self.sessions[session_id]["status"] = current_status
            
            self.logger.debug(f"会话 {session_id} 状态: {current_status}")
            
            # 处理不同状态
            if current_status == "completed":
                self.logger.info(f"语音生成完成: {session_id}")
                self._delete_session(session_id)
                
            elif current_status in ["stopped", "killed", "error"]:
                self.logger.warning(f"会话异常结束: {session_id}, 状态: {current_status}")
                self._delete_session(session_id)
                
            elif current_status == "playing":
                self.logger.info(f"语音播放中: {session_id}")
                # playing 状态不需要删除，继续监控
                
            # generating 状态继续监控
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"检查会话状态失败 {session_id}: {e}")
            # 网络错误时保留会话，下次重试

    def _delete_session(self, session_id: str):
        """
        删除会话
        
        Args:
            session_id: 会话ID
        """
        url = f"{self.base_url}/api/sessions/{session_id}"
        headers = {
            'accept': 'application/json'
        }
        
        try:
            response = requests.delete(url, headers=headers, timeout=5)
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") == "deleted":
                self.logger.info(f"会话已删除: {session_id}")
                if session_id in self.sessions:
                    del self.sessions[session_id]
            else:
                self.logger.warning(f"删除会话失败: {session_id}, 响应: {result}")
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"删除会话请求失败 {session_id}: {e}")
            # 删除失败，但仍然从监控列表中移除
            if session_id in self.sessions:
                del self.sessions[session_id]

    def get_session_status(self, session_id: str) -> Optional[str]:
        """
        获取指定会话的当前状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话状态，如果会话不存在则返回None
        """
        session = self.sessions.get(session_id)
        return session.get("status") if session else None

    def get_all_sessions(self) -> Dict[str, Dict]:
        """
        获取所有活跃会话
        
        Returns:
            所有会话信息的字典
        """
        return self.sessions.copy()

    def stop_monitoring(self):
        """停止监控线程"""
        self._stop_monitoring = True
        if self.monitor_thread and self.monitor_thread.is_alive() and self.monitor_thread.ident != threading.current_thread().ident:
            self.monitor_thread.join(timeout=5)
        self.logger.info("会话监控线程已停止")

    def __del__(self):
        """析构函数，确保线程被正确停止"""
        self.stop_monitoring()


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