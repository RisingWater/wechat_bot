import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from config import ConfigManager
from zhdate import ZhDate
from detector.reminder_loop import ReminderLoop
from detector.dsm_loop import DsmLoop

# 设置日志
logger = logging.getLogger(__name__)

class DetectorLoop:
    def __init__(self, wxauto_client, env_file: str = ".env"):
        self._env_file = env_file
        self._running = False
        self.processors = {}
        self.wxauto_client = wxauto_client
        self._init_processors(self._env_file)

    def _init_processors(self, env_file):
        self.register_processor("reminder_loop", ReminderLoop(self.wxauto_client, env_file))
        logger.info("注册提醒检查处理器...")

        self.register_processor("dsm_loop", DsmLoop(self.wxauto_client, env_file))
        logger.info("注册DSM开门记录处理器...")

    def register_processor(self, name: str, processor_instance):
        """注册处理器"""
        self.processors[name] = processor_instance
    
    def start_loop(self, check_interval: int = 60):
        """启动检测器循环"""
        self._running = True
        logger.info(f"检测循环启动，检查间隔: {check_interval}秒")

        config_manager = ConfigManager(self._env_file)
      
        try:
            while self._running:
                try:
                    # 循环处理所有注册的检测器
                    for name, processor in self.processors.items():
                        if hasattr(processor, "process_loop"):
                            processor.process_loop(config_manager)

                    time.sleep(check_interval)
                    
                except KeyboardInterrupt:
                    logger.info("收到中断信号，停止检测器循环")
                    break
                except Exception as e:
                    logger.error(f"检测器循环出错: {e}")
                    time.sleep(check_interval)  # 出错后继续运行
                    
        finally:
            self._running = False
            logger.info("检测器循环已停止")
    
    def stop_loop(self):
        """停止检测器循环"""
        self._running = False
        logger.info("正在停止检测器循环...")

# 独立运行
if __name__ == "__main__":
    import sys
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('detector_loop.log', encoding='utf-8')
        ]
    )
    
    try:
        reminder_loop = DetecorLoop()
        reminder_loop.start_loop(check_interval=60)  # 每分钟检查一次
        
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        sys.exit(1)