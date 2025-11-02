import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from config import ConfigManager
from env import EnvConfig
from typing import Any, Dict, List, , TypeVar, Generic

# 请求数据模型
class AddChatNameRequest(BaseModel):
    chat_name: str

class UpdateProcessorsRequest(BaseModel):
    processors: List[str]  # 处理器列表，如 ["license_processor", "mitv_processor", "chat_processor"]

class UpdateRemindersRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    calendar_type: Optional[str] = None  # "solar" 或 "lunar"
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    enabled: Optional[bool] = None

class WebServer:
    def __init__(self, env_file=".env"):
        self._config = EnvConfig(env_file)
        self._config_manager = ConfigManager(env_file)
        self._app = FastAPI()
        self._server = None
        self._setup_routes()
    
    @property
    def app(self):
        """提供对 FastAPI 应用的访问"""
        return self._app
    
    def _setup_routes(self):
        """设置路由"""
        @self._app.get("/")
        async def hello_world():
            return {"message": "Hello World!"}
        
        ## 处理器
        @self._app.get("/processors")
        async def list_processors():
            return self._config_manager.get_all_processors()

        ## 聊天列表对应的处理器
        @self._app.get("/chatname_processors")
        async def list_chatname_processors():
            return self._config_manager.get_all_chatname_processors()

        @self._app.post("/chatname_processors")
        async def add_chatname_processor(request: dict):
            """添加 chatname_processor"""
            chat_name = request.get('chat_name')
            if not chat_name:
                return {
                    "status": "failed",
                    "message": "chat_name 不能为空"
                }

            success, message = self._config_manager.add_chatname(chat_name)
            
            if success:
                return {
                    "status": "success",
                    "message": message
                }
            else:
                return {
                    "status": "failed",
                    "message": message
                }

        @self._app.put("/chatname_processors/{chat_name}")
        async def update_chatname_processor(chat_name: str, request: dict):
            """更新 chatname_processor"""
            success, message = self._config_manager.update_chatname(chat_name, request.get('processors', []))
            
            if success:
                return {
                    "status": "success", 
                    "message": message
                }
            else:
                return {
                    "status": "failed",
                    "message": message
                }
            

        @self._app.delete("/chatname_processors/{chat_name}")
        async def delete_chatname_processor(chat_name: str):
            """删除 chatname_processor"""
            success, message = self._config_manager.del_chatname(chat_name)
            
            if success:
                return {
                    "status": "success", 
                    "message": message
                }
            else:
                return {
                    "status": "failed",
                    "message": message
                }

        ## 提醒    
        @self._app.get("/reminders")
        async def list_reminders():
            """获取所有提醒"""
            reminders = self._config_manager.get_all_reminders()
            return {
                "status": "success",
                "data": reminders
            }
        
        @self._app.post("/reminders")
        async def add_reminder(request: dict):
            """添加提醒"""
            success, message = self._config_manager.add_reminder(request)
            if success:
                return {
                    "status": "success",
                    "message": message
                }
            else:
                return {
                    "status": "failed", 
                    "message": message
                }

        @self._app.put("/reminders/{reminder_id}")
        async def update_reminder(reminder_id: int, request: dict):
            """更新提醒"""
            success, message = self._config_manager.update_reminder(reminder_id, request)
            if success:
                return {
                    "status": "success",
                    "message": message
                }
            else:
                return {
                    "status": "failed",
                    "message": message
                }

        @self._app.delete("/reminders/{reminder_id}")
        async def delete_reminder(reminder_id: int):
            """删除提醒"""
            success, message = self._config_manager.delete_reminder(reminder_id)
            
            if success:
                return {
                    "status": "success",
                    "message": message
                }
            else:
                return {
                    "status": "failed",
                    "message": message
            }
            
    async def start(self):
        """异步启动服务器"""
        web_config = uvicorn.Config(self._app, host="0.0.0.0", port=6017)
        self._server = uvicorn.Server(web_config)
        await self._server.serve()
    
    def start_sync(self):
        """同步启动服务器（简单方式）"""
        uvicorn.run(self._app, host="0.0.0.0", port=6017)

# 使用方式
if __name__ == "__main__":
    server = WebServer()
    server.start_sync()
    
    # 方式2：异步启动（需要在异步环境中）
    # import asyncio
    # asyncio.run(server.start())