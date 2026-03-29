import time
import json
import logging
import threading
from datetime import datetime, time as dt_time
from typing import List, Dict, Any
from config import ConfigManager
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
        self._interval = 86400  # 默认每天检查一次（24小时）
        self._check_time = dt_time(20, 30)  # 每天20:30检查
        self._last_notified_devices = {}  # 记录上次通知的设备电量状态
        self._low_battery_threshold = 30  # 低电量阈值30%
    
    def process_loop(self, config_manager):
        """处理电量检测"""
        current_time = time.time()
        time_since_last = current_time - self._last_process_time
        
        # 检查是否到了每天的检查时间
        now = datetime.now()
        should_check = False
        
        # 如果距离上次检查超过24小时，或者现在是20:30之后且今天还没检查过
        if time_since_last >= self._interval:
            should_check = True
        elif now.time() >= self._check_time:
            # 检查今天是否已经检查过
            last_check_date = datetime.fromtimestamp(self._last_process_time).date()
            if last_check_date < now.date():
                should_check = True
        
        if not should_check:
            return
        
        # 更新上次执行时间
        self._last_process_time = current_time

        logger.info(f"开始处理battery_loop任务，检查时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # 创建QBLocation实例获取设备电量信息
            qb_location = QBLocation(self._env_file)
            devices = qb_location.get_power()
            
            if not devices:
                logger.warning("未能获取到设备电量信息")
                return
            
            logger.info(f"获取到 {len(devices)} 个设备的电量信息")
            
            # 检查每个设备的电量
            low_battery_devices = []
            for device in devices:
                device_id = device.get("device_id")
                device_name = device.get("device_name", "未知设备")
                power = device.get("power", 100)  # 默认100%以防数据缺失
                
                # 检查电量是否低于阈值
                if power < self._low_battery_threshold:
                    # 使用设备ID作为唯一标识
                    device_key = f"{device_id}"
                    
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
                        logger.info(f"设备 {device_name} 电量 {power}% 低于阈值，需要通知")
                    else:
                        logger.info(f"设备 {device_name} 电量 {power}% 已通知过，跳过")
                else:
                    # 如果电量恢复正常，清除通知记录
                    device_key = f"{device_id}"
                    if device_key in self._last_notified_devices:
                        logger.info(f"设备 {device_name} 电量已恢复至 {power}%，清除通知记录")
                        del self._last_notified_devices[device_key]
            
            # 如果有低电量设备，发送通知
            if low_battery_devices:
                self._send_low_battery_notification(low_battery_devices)
            else:
                logger.info("所有设备电量正常")
                
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
    
    def set_check_time(self, hour: int, minute: int):
        """设置每天检查的时间"""
        self._check_time = dt_time(hour, minute)
        logger.info(f"电量检测时间设置为 {hour:02d}:{minute:02d}")