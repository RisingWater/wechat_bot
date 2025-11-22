import time
import json
import logging
import threading
from datetime import datetime
from typing import List, Dict, Any
from config import ConfigManager
from zhdate import ZhDate
from webapi.dsmxp import DSMSmartDoorAPI
from webapi.audio_player import AudioPlayer

# 设置日志
logger = logging.getLogger(__name__)

router_data = [
    {
        "name" : "乔宝", 
        "detectors" : [
            { 
                "chatname" : "学霸乔宝专项配套办公室",
                "type" : "notify"
            }
        ]
    },
    {
        "name" : "顶子", 
        "detectors" : [
            { 
                "text" : "王旭，欢迎回家",
                "type" : "audio_play"
            }
        ]
    }
]

class DsmLoop:
    def __init__(self, wxauto_client, env_file: str = ".env"):
        self._env_file = env_file
        self._running = False
        self.wxauto_client = wxauto_client
        self._dsmxp = DSMSmartDoorAPI(env_file)
        self._last_process_time = time.time()
        self._interval = 180
        self._default_interval = 180
        self._restore_timer = None
    
    def set_interval(self, interval: int):
        old_interval = self._interval
        logger.info(f"间隔从 {old_interval}秒 临时调整为 {interval}秒，10分钟后恢复")
        self._interval = interval
    
        if self._restore_timer:
            self._restore_timer.cancel()

        # 使用 threading.Timer 更简洁
        def restore_interval():
            self._interval = self._default_interval
            logger.info(f"间隔已恢复为默认值: {self._default_interval}秒")
            self._restore_timer = None

        self._restore_timer = threading.Timer(600, restore_interval)  # 600秒 = 10分钟
        self._restore_timer.daemon = True
        self._restore_timer.start()

    def process_loop(self, config_manager):
        """处理所有提醒"""
        current_time = time.time()
        time_since_last = current_time - self._last_process_time
        if time_since_last < self._interval:
            return
        
        # 更新上次执行时间
        self._last_process_time = current_time

        logger.info("开始处理dsm_loop 任务")

        try:
            send_msg = False
            loglist = self._dsmxp.get_log()
            
            for log in loglist:
                name = log.get("name")
                timestamp = log.get("timestamp")
                if not config_manager.get_dsm_log(timestamp, name):
                    logger.info(f"发现新开门记录: {timestamp}")
                    config_manager.add_dsm_log(timestamp, name)

                    for route in router_data:
                        if route["name"] == "*" or route["name"] == name:
                            for detector in route["detectors"]:
                                if detector["type"] == "notify":
                                    msg = f"🎉🎉🎉 {name} 于 {timestamp.split(' ')[1]} 到家啦"
                                    self.wxauto_client.send_text_message(detector["chatname"], msg)
                                    send_msg = True
                                    break
                                elif detector["type"] == "audio_play":
                                    AudioPlayer().speak(detector["text"])
                                    send_msg = True
                                    break
                    
            if send_msg and self._interval != self._default_interval:
                self._interval = self._default_interval
                logger.info(f"恢复 dsm_loop 检测间隔为默认值 {self._default_interval} 秒")
                if self._restore_timer:
                    self._restore_timer.cancel()
                    self._restore_timer = None
        except Exception as e:
            logger.error(f"处理提醒时出错: {e}")
    