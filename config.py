from db.sqlite import SQLiteDatabase
from db.base import QueryResult, QueryParams
import logging
import json
from env import EnvConfig
from typing import List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, env_file=".env") -> None:
        self._db = SQLiteDatabase(env_file)
        logger.info("ConfigManager initialized")

    def init_table(self):
        self._init_kv_table()
        self._init_processsors_table()
        self._init_chatname_processors_table()
        self._init_reminders_table()
        self._init_dsm_log_table()
        self._init_exam_table()

    def _init_kv_table(self):
        self._db.create_table("kv", {
            "id": "TEXT PRIMARY KEY",
            "value": "TEXT",
        })

    def _init_exam_table(self):
        self._db.create_table("qb_exam", {
            "id": "TEXT PRIMARY KEY",
            "examId": "TEXT NOT NULL",
            "paperName": "TEXT NOT NULL",
            "subjectName": "TEXT NOT NULL",
            "userScore" : "REAL",
            "standardScore" : "REAL",
        })

    def _init_dsm_log_table(self):
        self._db.create_table("dsm_log", {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",  # 自增主键
            "timestamp": "TEXT NOT NULL",               # 时间戳
            "name": "TEXT NOT NULL",                 # 日志消息
        })

    def _init_processsors_table(self):
        self._db.create_table("processors", {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL UNIQUE",
            "description": "TEXT",
        })

    def _init_reminders_table(self):
        self._db.create_table("reminders", {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",  # 自增主键
            "title": "TEXT NOT NULL",                   # 提醒标题
            "description": "TEXT",                      # 详细描述
            "calendar_type": "TEXT NOT NULL",           # 日历类型: solar(公历)/lunar(农历)
            
            # 日期字段 - 公历和农历共用
            "year": "INTEGER",                          # 年份 NULL表示每年
            "month": "INTEGER",                         # 月份 (1-12)，NULL表示每月
            "day": "INTEGER",                           # 日期 (1-31)，NULL表示每天
            
            # 时间设置
            "hour": "INTEGER NOT NULL DEFAULT 8",       # 小时 (0-23)
            "minute": "INTEGER NOT NULL DEFAULT 0",     # 分钟 (0-59)
            
            "enabled": "BOOLEAN NOT NULL DEFAULT 1",    # 是否启用
            "chatnames": "TEXT NOT NULL ",
        })

    def _init_chatname_processors_table(self):
        self._db.create_table("chatname_processors", {
            "id": "TEXT PRIMARY KEY",
            "chat_name": "TEXT NOT NULL UNIQUE",
            "processors": "TEXT",
        })

    def update_processor(self, processor_name: str, processor_description: str):
        current_processor = {
            "id" : processor_name,
            "name" : processor_name,
            "description" : processor_description
        }

        param = QueryParams(
            filters={"id": processor_name},
        )

        result = self._db.query("processors", param)
        if result.total > 0:
            logger.info(f"处理器 {processor_name} 已经存在, 更新处理器信息")
            self._db.update("processors", processor_name, current_processor)
        else:
            logger.info(f"处理器 {processor_name} 不存在, 插入处理器信息")
            self._db.insert("processors", current_processor)

    def get_all_processors(self):
        query_all_param = QueryParams()
        result = self._db.query("processors", query_all_param)
        logger.info(json.dumps(result.items, ensure_ascii=False, indent=2))
        return result.items

    def find_processor(self, chat_name: str) -> List:
        processors = []
        query_param = QueryParams(filters={"chat_name": chat_name})
        result = self._db.query("chatname_processors", query_param)
        if result.total > 0:
            processors_str = result.items[0].get("processors")
            processors = json.loads(processors_str)

        return processors

    def get_all_chatname_processors(self):
        query_all_param = QueryParams()
        result = self._db.query("chatname_processors", query_all_param)
        logger.info(json.dumps(result.items, ensure_ascii=False, indent=2))
        return result.items

    def update_chatname(self, chat_name: str, processors: List[str]) -> Tuple[bool, str]:
        chatname_processors = {
            "id" : chat_name,
            "chat_name" : chat_name,
            "processors" : json.dumps(processors, ensure_ascii=False)
        }

        param = QueryParams(
            filters={"chat_name": chat_name},
        )

        result = self._db.query("chatname_processors", param)
        if result.total == 0:
            logger.info(f"{chat_name} 不存在, 无法更新")
            return False, "名称不存在"
        else:
            logger.info(f"{chat_name} 已经存在, 更新")
            self._db.update("chatname_processors", chat_name, chatname_processors)
            return True, "更新成功" 
        
    def add_chatname(self, chat_name: str) -> Tuple[bool, str]:
        chatname_processors = {
            "id" : chat_name,
            "chat_name" : chat_name,
            "processors" : "[]"
        }

        param = QueryParams(
            filters={"chat_name": chat_name},
        )

        result = self._db.query("chatname_processors", param)
        if result.total > 0:
            logger.info(f"{chat_name} 已经存在, 忽略添加")
            return False, "名称已经存在"
        else:
            logger.info(f"{chat_name} 不存在, 添加")
            self._db.insert("chatname_processors", chatname_processors)
            return True, "添加成功"

    def del_chatname(self, chat_name: str) -> Tuple[bool, str]:
        result = self._db.delete("chatname_processors", chat_name)
        if (result):
            logger.info(f"{chat_name} 删除成功")
            return True, "删除成功"
        else:
            logger.info(f"{chat_name} 删除失败")
            return False, "删除失败"

    def get_all_reminders(self):
        query_all_param = QueryParams()
        result = self._db.query("reminders", query_all_param)
        return result.items
        
    def add_reminder(self, reminder_data: dict) -> Tuple[bool, str]:
        """
        添加提醒
        """
        # 必填字段验证
        if not reminder_data.get('title'):
            return False, "标题不能为空"
        
        if not reminder_data.get('calendar_type') or reminder_data['calendar_type'] not in ['solar', 'lunar']:
            return False, "日历类型必须为 solar 或 lunar"
        
        # 设置默认值
        defaults = {
            'description': '提醒',
            'year': None,
            'month': None,
            'day': None,
            'hour': 8,
            'minute': 0,
            'enabled': True,
            'chatnames': []
        }
        
        # 合并数据
        data = defaults.copy()
        data.update(reminder_data)
        
        try:
            self._db.insert("reminders", data)
            logger.info(f"提醒 '{reminder_data['title']}' 添加成功")
            return True, "添加成功"
        except Exception as e:
            logger.error(f"添加提醒失败: {str(e)}")
            return False, f"添加失败: {str(e)}"
        
    def update_reminder(self, reminder_id: int, update_data: dict) -> Tuple[bool, str]:
        """
        更新提醒
        
        Args:
            reminder_id (int): 要更新的提醒ID
            update_data (dict): 要更新的字段数据
        """
        if not reminder_id:
            return False, "提醒ID不能为空"
        
        # 验证提醒是否存在
        param = QueryParams(
            filters={"id": reminder_id},
        )
        result = self._db.query("reminders", param)
        if result.total == 0:
            logger.info(f"提醒ID {reminder_id} 不存在")
            return False, "提醒不存在"
        
        # 数据验证
        if 'calendar_type' in update_data and update_data['calendar_type'] not in ['solar', 'lunar']:
            return False, "日历类型必须为 solar 或 lunar"
        
        if 'year' in update_data and update_data['year'] is not None and update_data['year'] < 1900:
            return False, "年份不能小于1900"
        
        if 'month' in update_data and update_data['month'] is not None and not (1 <= update_data['month'] <= 12):
            return False, "月份必须在 1-12 范围内"
        
        if 'day' in update_data and update_data['day'] is not None and not (1 <= update_data['day'] <= 31):
            return False, "日期必须在 1-31 范围内"
        
        if 'hour' in update_data and not (0 <= update_data['hour'] <= 23):
            return False, "小时必须在 0-23 范围内"
        
        if 'minute' in update_data and not (0 <= update_data['minute'] <= 59):
            return False, "分钟必须在 0-59 范围内"
        
        try:
            self._db.update("reminders", reminder_id, update_data)
            logger.info(f"提醒ID {reminder_id} 更新成功")
            return True, "更新成功"
        except Exception as e:
            logger.error(f"更新提醒失败: {str(e)}")
            return False, f"更新失败: {str(e)}"
    def delete_reminder(self, reminder_id: int) -> Tuple[bool, str]:
        result = self._db.delete("reminders", reminder_id)
        if (result):
            logger.info(f"{reminder_id} 删除成功")
            return True, "删除成功"
        else:
            logger.info(f"{reminder_id} 删除失败")
            return False, "删除失败"

    def add_dsm_log(self, timestamp: str, name: str) -> Tuple[bool, str]:
        """
        添加DSM日志记录
        """
        log_data = {
            "timestamp": timestamp,
            "name": name
        }
        
        try:
            self._db.insert("dsm_log", log_data)
            logger.info(f"DSM日志记录添加成功: {timestamp} - {name}")
            return True, "添加成功"
        except Exception as e:
            logger.error(f"添加DSM日志记录失败: {str(e)}")
            return False, f"添加失败: {str(e)}"

    def get_dsm_log(self, timestamp: str, name: str) -> bool:
        """
        判断DSM日志记录是否存在
        """
        param = QueryParams(
            filters={
                "timestamp": timestamp,
                "name": name
            }
        )

        try:
            result = self._db.query("dsm_log",param)
            if result.total > 0:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"获取DSM日志记录失败: {str(e)}")
            return False

    def del_all_dsm_log(self) -> Tuple[bool, str]:
        """
        删除所有DSM日志记录
        """
        try:
            self._db.delete_all("dsm_log")
            logger.info(f"删除所有DSM日志记录成功")
            return True, "删除成功"
        except Exception as e:
            logger.error(f"删除DSM日志记录失败: {str(e)}")
            return False, f"删除失败: {str(e)}"

    def get_value(self, key: str) -> str:
        """
        获取配置项的值
        """
        param = QueryParams(
            filters={"id": key},
        )
        result = self._db.query("kv", param)
        if result.total == 0:
            return ""
        else:
            return result.data[0]["value"]
        
    def put_value(self, key: str, value: str):
        """
        设置配置项的值
        """
        self._db.update("kv", key, {"value": value})

    def get_qbexam(self, paperId: str):
        """
        获取配置项的值
        """
        param = QueryParams(
            filters={"id": paperId},
        )
        result = self._db.query("qb_exam", param)
        if result.total == 0:
            return None
        else:
            return result.data[0]
        
    def put_qbexam(self, exam_report) -> Tuple[bool, str]:
        data = {
            "id" : str(exam_report["paperId"]),
            'examId' : str(exam_report['examId']),
            "paperName" : str(exam_report['paperName']),
            "subjectName" : str(exam_report['subjectName']),
            "userScore" : float(exam_report['userScore']),
            "standardScore" : float(exam_report['standardScore']),
        }

        param = QueryParams(
            filters={"id": str(exam_report["paperId"])},
        )

        result = self._db.query("qb_exam", param)
        if result.total > 0:
            logger.info(f"考试 {exam_report["paperId"]} 已经存在, 更新")
            self._db.update("qb_exam", str(exam_report["paperId"]), data)
        else:
            logger.info(f"考试 {exam_report["paperId"]} 不存在, 新增")
            self._db.insert("qb_exam", data)

        return True, "操作成功"


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    sqllite = ConfigManager()
    result = sqllite.find_processor("王旭")
    logging.info(result[0])
    logging.info(result[1])
    logging.info(result[2])
        
