import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from config import ConfigManager
from zhdate import ZhDate

# 设置日志
logger = logging.getLogger(__name__)

class ReminderLoop:
    def __init__(self, wxauto_client, env_file: str = ".env"):
        self._env_file = env_file
        self._running = False
        self.wxauto_client = wxauto_client
    
    def _get_current_lunar_date(self) -> tuple:
        """获取当前农历日期"""
        try:
            current_time = datetime.now()
            lunar_date = ZhDate.from_datetime(current_time)
            return lunar_date.lunar_year, lunar_date.lunar_month, lunar_date.lunar_day
        except Exception as e:
            logger.error(f"获取农历日期失败: {e}")
            # 失败时返回公历日期作为fallback
            current_time = datetime.now()
            return current_time.year, current_time.month, current_time.day
    
    def _get_current_solar_date(self) -> tuple:
        """获取当前公历日期"""
        current_time = datetime.now()
        return current_time.year, current_time.month, current_time.day
    
    def _should_trigger_reminder(self, reminder: Dict[str, Any]) -> bool:
        """检查提醒是否应该触发"""
        try:
            # 检查是否启用
            if not reminder.get('enabled', True):
                return False
            
            current_time = datetime.now()
            current_hour = current_time.hour
            current_minute = current_time.minute
            
            # 检查时间是否匹配
            if current_hour != reminder.get('hour', 0) or current_minute != reminder.get('minute', 0):
                return False
            
            # 获取日历信息
            calendar_type = reminder.get('calendar_type', 'solar')
            reminder_month = reminder.get('month')
            reminder_day = reminder.get('day')
            
            # 根据日历类型获取当前日期
            if calendar_type == 'solar':
                current_year, current_month, current_day = self._get_current_solar_date()
                calendar_name = "公历"
            else:  # lunar
                current_year, current_month, current_day = self._get_current_lunar_date()
                calendar_name = "农历"
            
            logger.debug(f"{calendar_name}日期: {current_year}年{current_month}月{current_day}日")
            
            # 检查日期匹配
            # 如果月份为 None，表示每月都提醒
            if reminder_month is not None and current_month != reminder_month:
                logger.debug(f"月份不匹配: 当前{current_month}月, 需要{reminder_month}月")
                return False
            
            # 如果日期为 None，表示每天都提醒
            if reminder_day is not None and current_day != reminder_day:
                logger.debug(f"日期不匹配: 当前{current_day}日, 需要{reminder_day}日")
                return False
            
            logger.info(f"提醒匹配: {reminder.get('title')} - {calendar_name}{current_month}月{current_day}日 {current_hour:02d}:{current_minute:02d}")
            return True
            
        except Exception as e:
            logger.error(f"检查提醒时出错: {e}")
            return False
    
    def _send_reminder(self, reminder: Dict[str, Any]):
        """发送提醒"""
        try:
            title = reminder.get('title', '提醒')
            description = reminder.get('description', '')
            chatnames_str = reminder.get('chatnames', '[]')
            calendar_type = reminder.get('calendar_type', 'solar')
            
            # 解析联系人列表
            chatnames = []
            if chatnames_str:
                try:
                    chatnames = json.loads(chatnames_str)
                except json.JSONDecodeError:
                    logger.error(f"解析联系人列表失败: {chatnames_str}")
                    return
            
            # 构建提醒消息
            calendar_text = "农历" if calendar_type == 'lunar' else "公历"
            current_time = datetime.now().strftime("%H:%M")
            
            message = f"🔔 {title}\n"
            message += f"⏰ 时间: {calendar_text} {current_time}\n"
            
            if description:
                message += f"📝 {description}\n"
            
            # 添加日期信息
            if calendar_type == 'solar':
                year, month, day = self._get_current_solar_date()
                message += f"📅 公历: {month}月{day}日"
            else:
                year, month, day = self._get_current_lunar_date()
                message += f"📅 农历: {month}月{day}日"
            
            logger.info(f"发送提醒: {message}")
            logger.info(f"发送给: {chatnames}")
            
            for chatname in chatnames:
                self.wxauto_client.send_text_message(who=chatname, msg=message)
                
        except Exception as e:
            logger.error(f"发送提醒时出错: {e}")
    
    def _format_reminder_info(self, reminder: Dict[str, Any]) -> str:
        """格式化提醒信息用于日志"""
        title = reminder.get('title', '未知')
        calendar_type = "农历" if reminder.get('calendar_type') == 'lunar' else "公历"
        month = "每月" if reminder.get('month') is None else f"{reminder['month']}月"
        day = "每天" if reminder.get('day') is None else f"{reminder['day']}日"
        time_str = f"{reminder.get('hour', 0):02d}:{reminder.get('minute', 0):02d}"
        
        return f"{title} ({calendar_type} {month}{day} {time_str})"
    
    def _process_reminders(self, config_manager):
        """处理所有提醒"""
        try:
            reminders = config_manager.get_all_reminders()
            
            triggered_count = 0
            for reminder in reminders:
                reminder_info = self._format_reminder_info(reminder)
                if self._should_trigger_reminder(reminder):
                    logger.info(f"触发提醒: {reminder_info}")
                    self._send_reminder(reminder)
                    triggered_count += 1
            
            if triggered_count > 0:
                logger.info(f"本次检查触发了 {triggered_count} 个提醒")
                    
        except Exception as e:
            logger.error(f"处理提醒时出错: {e}")
    
    def start_loop(self, check_interval: int = 60):
        """启动提醒循环"""
        self._running = True
        logger.info(f"提醒循环启动，检查间隔: {check_interval}秒")

        config_manager = ConfigManager(self._env_file)
        
        # 测试农历功能
        try:
            lunar_year, lunar_month, lunar_day = self._get_current_lunar_date()
            solar_year, solar_month, solar_day = self._get_current_solar_date()
            logger.info(f"当前公历: {solar_year}年{solar_month}月{solar_day}日")
            logger.info(f"当前农历: {lunar_year}年{lunar_month}月{lunar_day}日")
        except Exception as e:
            logger.warning(f"农历功能测试失败: {e}")
        
        try:
            while self._running:
                try:
                    self._process_reminders(config_manager)
                    time.sleep(check_interval)
                    
                except KeyboardInterrupt:
                    logger.info("收到中断信号，停止提醒循环")
                    break
                except Exception as e:
                    logger.error(f"提醒循环出错: {e}")
                    time.sleep(check_interval)  # 出错后继续运行
                    
        finally:
            self._running = False
            logger.info("提醒循环已停止")
    
    def stop_loop(self):
        """停止提醒循环"""
        self._running = False
        logger.info("正在停止提醒循环...")

# 独立运行
if __name__ == "__main__":
    import sys
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('reminder_loop.log', encoding='utf-8')
        ]
    )
    
    try:
        reminder_loop = ReminderLoop()
        reminder_loop.start_loop(check_interval=60)  # 每分钟检查一次
        
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        sys.exit(1)