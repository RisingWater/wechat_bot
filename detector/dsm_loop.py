import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from config import ConfigManager
from zhdate import ZhDate
from webapi.dsmxp import DSMSmartDoorAPI

# 设置日志
logger = logging.getLogger(__name__)

router_data = [
    {
        "name" : "乔宝", 
        "detectors" : [
            { 
                "chatname" : "王旭", #"学霸乔宝专项配套办公室",
                "type" : "notify"
            }
        ]
    }
    #,
    #{
    #    "name" : "*", 
    #    "detectors" : [
    #        { 
    #            "chatname" : "王旭",
    #            "type" : "notify"
    #        }
    #    ]
    #}
]

class DsmLoop:
    def __init__(self, wxauto_client, env_file: str = ".env"):
        self._env_file = env_file
        self._running = False
        self.wxauto_client = wxauto_client
        self._dsmxp = DSMSmartDoorAPI(env_file)
    
    def process_loop(self, config_manager):
        """处理所有提醒"""
        try:
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
                                    msg = f"🎉🎉🎉 {name} 于 {timestamp} 到家啦"
                                    self.wxauto_client.send_text_message(detector["chatname"], msg)
                                    break
                    
        except Exception as e:
            logger.error(f"处理提醒时出错: {e}")
    