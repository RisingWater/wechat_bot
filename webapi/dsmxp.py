# deepseek.py
import requests
import json
import logging
import hashlib
import re
from typing import List, Tuple  # 添加缺失的导入
from env import EnvConfig

logger = logging.getLogger(__name__)

class DSMSmartDoorAPI:
    def __init__(self, env_file=".env"):
        self._env_file = env_file
        self._config = EnvConfig(env_file)
        self._token = None
        self._load_config()
        print(f"登录成功，Token: {self._token}")

    def _load_config(self):
        dsm_config = self._config.get_dsm_smart_door_config()
        self._token = dsm_config.get("token")
  
    def get_log(self) -> List:
        headers = {
            "token": self._token,
        }

        loglist = []

        get_log_url = "https://nyuwa.dsmxp.com/nyuwa/dc/lock/log/open/door/type?lockId=2023111816472300760&pageNum=1&pageSize=20&type=1"

        response = requests.get(get_log_url, headers=headers)
        if not response.status_code == 200:
            msg = f"获取开门记录失败，状态码: {response.status_code}"
            logger.error(msg)
            return loglist

        log_info = response.json()

        if not log_info.get("success"):
            msg = f"获取开门记录失败: {log_info.get('message', '未知错误1')}"
            logger.error(msg)
            return loglist


        if not log_info.get("status") == 1:
            msg = f"获取开门记录失败: {log_info.get('message', '未知错误2')}"
            logger.error(msg)
            return loglist

        log_data = log_info.get("data", {})

        for record in log_data:
            logDate = record.get("logDate")
            if record.get('dayTag') == '昨天':
                for detail in record.get('logDetails', []):
                    if detail.get('logType') == '指纹开门':
                        logTime = detail.get('logTime')
                        name = re.findall(r'【(.*?)】', detail.get('content', ''))
                        if name :
                            info ={
                                "name": name[0],
                                "timestamp": logDate + " " + logTime
                            }
                            loglist.append(info)

        return loglist
