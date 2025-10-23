from db.sqlite import SQLiteDatabase
from db.base import QueryResult, QueryParams
import logging
import json
from env import EnvConfig
from typing import List
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, env_file=".env") -> None:
        self._db = SQLiteDatabase(env_file)
        self._init_table()
        logger.info("ConfigManager initialized")

    def _init_table(self):
        self._init_processsors_table()
        self._init_chatname_processors_table()

    def _init_processsors_table(self):
        self._db.create_table("processors", {
            "id": "TEXT PRIMARY KEY",
            "name": "TEXT NOT NULL UNIQUE",
            "description": "TEXT",
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

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    sqllite = ConfigManager()
    result = sqllite.find_processor("王旭")
    if result.total > 0:
        processors_str = result.items[0].get("processors")
        processors = json.loads(processors_str)
        for processor in processors:
            print(processor)
        