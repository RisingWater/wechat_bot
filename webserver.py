import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from config import ConfigManager
from env import EnvConfig
from webapi.wxauto import WXAuto
import os

from fastapi.middleware.cors import CORSMiddleware

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
    def __init__(self, wxauto_client, detector_loop, env_file=".env"):
        self.wxauto_client = wxauto_client
        self.detector_loop = detector_loop
        self._config = EnvConfig(env_file)
        self._env_file = env_file
        self._app = FastAPI()
        self._server = None
        self._setup_routes()
        self._setup_static_files()

        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],  # 你的前端地址
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_static_files(self):
        """设置静态文件服务"""
        # 构建路径指向 front/src/dist
        frontend_dist_path = os.path.join(os.path.dirname(__file__), "front", "src", "dist")
        
        if os.path.exists(frontend_dist_path):
            print(f"找到前端构建目录: {frontend_dist_path}")
            
            # 列出 dist 目录内容，帮助调试
            print("dist 目录内容:", os.listdir(frontend_dist_path))
            # 服务静态文件（CSS、JS、图片等）
            self._app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist_path, "assets")), name="assets")
            
            # 添加根路径路由，返回 index.html
            @self._app.get("/")
            async def serve_index():
                return FileResponse(os.path.join(frontend_dist_path, "index.html"))
            
            # 处理前端路由（SPA）
            @self._app.get("/{full_path:path}")
            async def serve_spa(full_path: str):
                # 检查请求的路径是否对应实际文件
                file_path = os.path.join(frontend_dist_path, full_path)
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    return FileResponse(file_path)
                # 否则返回 index.html（让前端路由处理）
                return FileResponse(os.path.join(frontend_dist_path, "index.html"))
        else:
            print(f"警告: 前端构建目录不存在: {frontend_dist_path}")

    @property
    def app(self):
        """提供对 FastAPI 应用的访问"""
        return self._app
    
    def _setup_routes(self):
        """设置路由"""
        
        ## 微信状态
        @self._app.get("/api/wechat_status")
        async def get_wechat_status():
            result = self.wxauto_client.is_online()
            if result["success"]:
                return {
                    "status": "success",
                    "data": result
                }
            else:
                return {
                    "status": "failed",
                    "data": result
                }

        @self._app.post("/api/wechat_login")
        async def get_wechat_status():
            result = self.wxauto_client.login()
            if result["success"]:
                return {
                    "status": "success",
                    "data": result
                }
            else:
                return {
                    "status": "failed",
                    "data": result
                }

        @self._app.get("/api/wechat_qrcode")
        async def get_wechat_qrcode():
            result = self.wxauto_client.get_qrcode()
            if result["success"]:
                return {
                    "status": "success",
                    "data": result
                }
            else:
                return {
                    "status": "failed",
                    "data": result
                }

        ## 处理器
        @self._app.get("/api/processors")
        async def list_processors():
            return ConfigManager(self._env_file).get_all_processors()

        ## 聊天列表对应的处理器
        @self._app.get("/api/chatname_processors")
        async def list_chatname_processors():
            return ConfigManager(self._env_file).get_all_chatname_processors()

        @self._app.post("/api/chatname_processors")
        async def add_chatname_processor(request: dict):
            """添加 chatname_processor"""
            chat_name = request.get('chat_name')
            if not chat_name:
                return {
                    "status": "failed",
                    "message": "chat_name 不能为空"
                }

            success, message = ConfigManager(self._env_file).add_chatname(chat_name)
            
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

        @self._app.put("/api/chatname_processors/{chat_name}")
        async def update_chatname_processor(chat_name: str, request: dict):
            """更新 chatname_processor"""
            success, message = ConfigManager(self._env_file).update_chatname(chat_name, request.get('processors', []))
            
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
            

        @self._app.delete("/api/chatname_processors/{chat_name}")
        async def delete_chatname_processor(chat_name: str):
            """删除 chatname_processor"""
            success, message = ConfigManager(self._env_file).del_chatname(chat_name)
            
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
        @self._app.get("/api/reminders")
        async def list_reminders():
            """获取所有提醒"""
            reminders = ConfigManager(self._env_file).get_all_reminders()
            print(reminders)
            return {
                "status": "success",
                "data": reminders
            }
        
        @self._app.post("/api/reminders")
        async def add_reminder(request: dict):
            """添加提醒"""
            success, message = ConfigManager(self._env_file).add_reminder(request)
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

        @self._app.put("/api/reminders/{reminder_id}")
        async def update_reminder(reminder_id: int, request: dict):
            """更新提醒"""
            success, message = ConfigManager(self._env_file).update_reminder(reminder_id, request)
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

        @self._app.delete("/api/reminders/{reminder_id}")
        async def delete_reminder(reminder_id: int):
            """删除提醒"""
            success, message = ConfigManager(self._env_file).delete_reminder(reminder_id)
            
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

        @self._app.get("/api/dsm_detected_interval_change")
        async def dsm_detected_interval_change(request: dict):
            """更新 DSM 检测间隔"""
            self.detector_loop.set_interval("dsm_loop", 5)
            return {
                "status": "success",
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
    wxauto = WXAuto()
    server = WebServer(wxauto)
    server.start_sync()
    
    # 方式2：异步启动（需要在异步环境中）
    # import asyncio
    # asyncio.run(server.start())