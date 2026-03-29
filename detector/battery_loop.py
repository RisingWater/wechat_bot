import time
import json
import logging
import threading
from datetime import datetime
from typing import List, Dict, Any
from config import ConfigManager
# 直接导入 QBLocation 避免平台依赖问题
try:
    from device.qb_location import QBLocation
except ImportError as e:
    # 如果导入失败，尝试直接导入模块
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from device.qb_location import QBLocation

router_data = [
    {
        "chatname" : "学霸乔宝专项配套办公室"
    },
]

# 设置日志
logger = logging.getLogger(__name__)

class BatteryLoop:
    def __init__(self, wxauto_client, env_file: str = ".env"):
        self._env_file = env_file
        self._running = False
        self.wxauto_client = wxauto_client
        self._last_process_time = time.time()
        self._interval = 3600  # 默认每小时检查一次
        self._restore_timer = None
        self._last_notified_devices = {}  # 记录上次通知的设备电量状态
        self._low_battery_threshold = 30  # 低电量阈值30%
    
    def process_loop(self, config_manager):
        """处理电量检测"""
        current_time = time.time()
        time_since_last = current_time - self._last_process_time
        if time_since_last < self._interval:
            return
        
        # 更新上次执行时间
        self._last_process_time = current_time

        logger.info("开始处理battery_loop 任务")

        try:
            # 创建QBLocation实例
            qb_location = QBLocation(self._env_file)
            
            # 登录获取token
            token = qb_location._login()
            if not token:
                logger.error("登录失败，无法获取设备信息")
                return
            
            # 直接获取设备列表
            device_list = qb_location._get_device_list(size=100, current=1)
            if not device_list or "records" not in device_list:
                logger.warning("未能获取到设备列表信息")
                return
            
            records = device_list["records"]
            if not records:
                logger.info("没有找到任何设备")
                return
            
            logger.info(f"获取到 {len(records)} 个设备的信息")
            
            # 检查每个设备的电量
            low_battery_devices = []
            for device in records:
                device_id = device.get("id")
                device_name = device.get("name", "未知设备")
                power = device.get("power", 100)  # 默认100%以防数据缺失
                
                # 检查电量是否低于阈值
                if power < self._low_battery_threshold:
                    # 使用设备ID作为唯一标识
                    device_key = f"{device_id}_{device_name}"
                    
                    # 检查是否已经通知过
                    last_notified_power = self._last_notified_devices.get(device_key)
                    
                    # 如果之前没有通知过，或者电量比上次通知时更低（避免重复通知）
                    if last_notified_power is None or power < last_notified_power:
                        low_battery_devices.append({
                            "device_id": device_id,
                            "device_name": device_name,
                            "power": power
                        })
                        # 更新记录
                        self._last_notified_devices[device_key] = power
                    else:
                        logger.info(f"设备 {device_name} 电量 {power}% 已通知过，跳过")
                else:
                    # 如果电量恢复正常，清除通知记录
                    device_key = f"{device_id}_{device_name}"
                    if device_key in self._last_notified_devices:
                        logger.info(f"设备 {device_name} 电量已恢复至 {power}%，清除通知记录")
                        del self._last_notified_devices[device_key]
            
            # 如果有低电量设备，发送通知
            if low_battery_devices:
                self._send_low_battery_notification(low_battery_devices)
            else:
                logger.info("所有设备电量正常")
                
            # 关闭会话
            qb_location.close()
                
        except Exception as e:
            logger.error(f"处理电量检测时出错: {e}")
    
    def _send_low_battery_notification(self, low_battery_devices):
        """发送低电量通知"""
        try:
            # 构建通知消息
            message = "⚠️ 低电量提醒 ⚠️\n\n"
            message += "以下设备电量低于30%，请及时充电：\n\n"
            
            for device in low_battery_devices:
                device_name = device["device_name"]
                power = device["power"]
                message += f"• {device_name}: {power}%\n"
            
            message += "\n请及时充电以确保设备正常工作。"
            
            # 发送到指定的群聊
            for route in router_data:
                chatname = route.get("chatname")
                if chatname:
                    if self.wxauto_client:
                        self.wxauto_client.send_text_message(chatname, message)
                        logger.info(f"已发送低电量提醒到群聊: {chatname}")
                    else:
                        logger.info(f"模拟发送低电量提醒到群聊: {chatname}")
                        logger.info(message)
                        
        except Exception as e:
            logger.error(f"发送低电量通知时出错: {e}")
    
    def set_interval(self, interval: int):
        """设置检查间隔（秒）"""
        self._interval = interval
        logger.info(f"电量检测间隔设置为 {interval} 秒")
    
    def set_low_battery_threshold(self, threshold: int):
        """设置低电量阈值（百分比）"""
        self._low_battery_threshold = threshold
        logger.info(f"低电量阈值设置为 {threshold}%")