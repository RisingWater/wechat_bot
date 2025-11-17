# deepseek.py
import requests
import json
import logging
from typing import Tuple  # 添加缺失的导入
from env import EnvConfig

logger = logging.getLogger(__name__)

class OpenDoorAPI:
    def __init__(self, env_file=".env"):
        self._config = EnvConfig(env_file)
        self._token = None
        self._location = None
        self._load_config()

    def _load_config(self):
        config = self._config.get_open_door_config()
        self._token = config.get("key")
        self._location = config.get("location")
        
        # 验证配置
        if not self._token:
            raise ValueError("未配置 token")
        if not self._location:
            raise ValueError("未配置 location")

    def open_door(self) -> Tuple[bool, str]:
        headers = {
            "Authorization": f"bearer {self._token}",
            "content-type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.65(0x18004129) NetType/4G Language/zh_CN",
            "Referer": "https://servicewechat.com/wx06875950b54784ee/51/page-frame.html"
        }

        logger.info("开始获取用户信息")
        
        try:
            # 1. 获取用户信息
            info_url = "https://property.admin.fjpy.cc/zone-cms/app-api/v1/cms/cmsOwnerBaseInfo/ownerWechat/info"
            response = requests.get(info_url, headers=headers, timeout=10)

            if response.status_code != 200:
                msg = f"获取用户信息失败，状态码: {response.status_code}"
                logger.error(msg)
                return False, msg

            user_info = response.json()
            if user_info.get("code") != "00000":
                msg = f"获取用户信息失败: {user_info.get('msg', '未知错误')}"
                logger.error(msg)
                return False, msg

            # 2. 遍历所有房产，获取设备列表
            owner_wechat_list = user_info["data"]["ownerWechatDTOList"]
            logger.info(f"找到 {len(owner_wechat_list)} 处房产")
            
            for owner in owner_wechat_list:
                residence_id = owner["residenceId"]
                logger.info(f"处理房产: {owner.get('buildingName', '')}{owner.get('unitName', '')}{owner.get('roomNo', '')}")
                
                # 3. 获取设备列表
                getlist_url = f"https://property.admin.fjpy.cc/zone-cms/app-api/v1/cms/cmsDeviceAccessControl/wechat/getList/{residence_id}"
                list_response = requests.get(getlist_url, headers=headers, timeout=10)
                
                if list_response.status_code != 200:
                    logger.warning(f"获取设备列表失败，状态码: {list_response.status_code}")
                    continue

                list_data = list_response.json()
                if list_data.get("code") != "00000":
                    logger.warning(f"获取设备列表失败: {list_data.get('msg', '未知错误')}")
                    continue

                # 4. 查找指定设备
                device_list = list_data.get("data", [])
                logger.info(f"找到 {len(device_list)} 个设备")
                
                for device in device_list:
                    device_name = device.get("locationName", "")
                    logger.debug(f"检查设备: {device_name}")
                    
                    if device_name == self._location:
                        device_id = device["id"]
                        logger.info(f"找到目标设备: {device_name}, ID: {device_id}")
                        
                        # 5. 开门请求 - 修复：使用 https
                        opendoor_url = f"https://property.admin.fjpy.cc/zone-cms/app-api/v1/cms/cmsDeviceAccessControl/wechat/openDoor/{device_id}"
                        opendoor_response = requests.get(opendoor_url, headers=headers, timeout=10)

                        if opendoor_response.status_code != 200:
                            msg = f"开门请求失败，状态码: {opendoor_response.status_code}"
                            logger.error(msg)
                            return False, msg

                        result = opendoor_response.json()
                        if result.get("code") == "00000":
                            msg = "开锁成功"
                            logger.info(msg)
                            return True, msg
                        else:
                            msg = f"开锁失败: {result.get('msg', '未知错误')}"
                            logger.error(msg)
                            return False, msg

            # 如果循环结束都没有找到设备
            msg = f"未找到设备名称为 '{self._location}' 的设备"
            logger.warning(msg)
            return False, msg
            
        except requests.exceptions.Timeout:
            msg = "请求超时"
            logger.error(msg)
            return False, msg
        except requests.exceptions.RequestException as e:
            msg = f"网络请求异常: {e}"
            logger.error(msg)
            return False, msg
        except Exception as e:
            msg = f"系统异常: {e}"
            logger.error(msg)
            return False, msg