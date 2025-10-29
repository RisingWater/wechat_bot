import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from config import ConfigManager
from env import EnvConfig

# 请求数据模型
class AddChatNameRequest(BaseModel):
    chat_name: str

class UpdateProcessorsRequest(BaseModel):
    processors: List[str]  # 处理器列表，如 ["license_processor", "mitv_processor", "chat_processor"]

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
        
        @self._app.get("/processors")
        async def list_processors():
            return self._config_manager.get_all_processors()

        @self._app.get("/chatname_processors")
        async def list_chatname_processors():
            return self._config_manager.get_all_chatname_processors()

        @self._app.post("/chatname_processors")
        async def add_chatname_processor(request: AddChatNameRequest):
            """添加 chatname_processor"""
            success, message = self._config_manager.add_chatname(
                request.chat_name,
            )
            
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
        async def update_chatname_processor(chat_name: str, request: UpdateProcessorsRequest):
            """删除 chatname_processor"""
            success, message = self._config_manager.update_chatname(chat_name, request.processors)
            
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
            
    async def start(self):
        """异步启动服务器"""
        web_config = uvicorn.Config(self._app, host="0.0.0.0", port=8000)
        self._server = uvicorn.Server(web_config)
        await self._server.serve()
    
    def start_sync(self):
        """同步启动服务器（简单方式）"""
        uvicorn.run(self._app, host="0.0.0.0", port=8000)

# 使用方式
if __name__ == "__main__":
    server = WebServer()
    server.start_sync()
    
    # 方式2：异步启动（需要在异步环境中）
    # import asyncio
    # asyncio.run(server.start())