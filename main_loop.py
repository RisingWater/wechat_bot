# main_loop.py
import os
import time
import logging
from pathlib import Path
from webapi.wxauto import WXAuto
from processor.homework_processor import HomeworkProcessor
from processor.print_processor import PrintProcessor
from processor.cmd_processor import CmdProcessor
from processor.chat_processor import ChatProcessor
from env import EnvConfig
from process_router import ProcessRouter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class MainLoopProcessor:
    def __init__(self, env_file=".env", config_file="processor_config.json"):
        """
        初始化主循环处理器
        
        Args:
            env_file (str): 环境配置文件路径
            config_file (str): 处理器配置文件路径
        """
        self._config = EnvConfig(env_file)
        self.wxauto = WXAuto(env_file)
        self.running = False
        
        # 初始化处理器路由
        self.process_router = self._init_process_router(env_file, config_file)
        
        logger.info("MainLoopProcessor 初始化完成")
        
    def _init_process_router(self, env_file, config_file):
        """
        初始化处理器路由
        
        Args:
            env_file (str): 环境配置文件路径
            config_file (str): 处理器配置文件路径
            
        Returns:
            ProcessRouter: 处理器路由实例
        """
        logger.info("正在初始化处理器路由...")
        router = ProcessRouter(config_file)
        
        # 注册所有处理器
        router.register_processor("homework_processor", HomeworkProcessor(env_file))
        logger.info("注册作业识别处理器...")

        router.register_processor("print_processor", PrintProcessor(env_file))
        logger.info("注册文件打印处理器...")

        router.register_processor("cmd_processor", CmdProcessor(env_file))
        logger.info("注册命令处理器...")

        router.register_processor("chat_processor", ChatProcessor(env_file))
        logger.info("注册聊天处理器...")
        
        logger.info("所有处理器注册完成")
        return router
    
    def main_loop(self, check_interval=3):
        """
        主循环
        
        Args:
            check_interval (int): 检查间隔秒数，默认3秒
        """
        self.running = True
        logger.info("=" * 50)
        logger.info("启动主循环处理器")
        logger.info(f"检查间隔: {check_interval}秒")
        logger.info("=" * 50)
        
        total_stats = {
            "processed": 0, 
            "errors": 0,
            "batches_processed": 0,
            "start_time": time.time()
        }
        
        try:
            while self.running:
                # 获取新消息
                message_result = self.wxauto.get_next_new_message()
                
                if not message_result.get("success"):
                    logger.warning(f"获取消息失败: {message_result.get('error')}")
                elif message_result.get("has_message"):
                    logger.info(f"发现新消息，来自: {message_result.get('chat_name')}")
                
                # 使用路由处理器处理消息
                self.process_router.route_message_batch(message_result, self.wxauto)
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("用户中断主循环")
        except Exception as e:
            logger.error(f"主循环发生错误: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            self.running = False
        
    def stop(self):
        """停止主循环"""
        logger.info("正在停止主循环...")
        self.running = False


def main():
    """主函数"""
    print("=" * 60)
    print("微信消息处理系统 - 主循环处理器")
    print("=" * 60)
    print("功能说明:")
    print("- 自动监控微信新消息")
    print("- 根据聊天名称路由到相应处理器")
    print("- 支持作业识别、文件打印、命令处理、聊天处理等功能")
    print("- 按配置文件精确匹配聊天名称")
    print("=" * 60)
    
    try:
        # 创建处理器实例
        processor = MainLoopProcessor(
            env_file=".env",
            config_file="processor_config.json"
        )
        
        # 启动主循环
        print("正在启动主循环...")
        print("按 Ctrl+C 可停止程序")
        print("-" * 40)
        
        processor.main_loop(check_interval=3)
        
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        print(f"错误: {e}")
        return 1
    
    print("程序正常退出")
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)