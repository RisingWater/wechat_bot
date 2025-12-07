# homework.py
import logging
import json
import uuid
import os
import shutil
import tempfile
import threading
import time
from utils.file_converter import FileConverter
from utils.file_recognize import FileRecognizer
from utils.image_binarize import ImageBinarrize
from config import ConfigManager
from device.print import Printer

logger = logging.getLogger(__name__)

class PrintProcessor:
    def __init__(self, env_file=".env"):
        self._converter = FileConverter()
        self._printer = Printer(env_file)
        self._file_recognize = FileRecognizer()
        self._photograph_print = False
        self._config_manager = ConfigManager(env_file)
        self._load_config()
        self.processor_name = "print_processor"
        logger.info(f"PrintProcessor initialized")
    
    def description(self) -> str:
        return "文档打印处理器"  
    
    def priority(self) -> int:
        return 10
    
    def _save_config(self):
        self._config_manager.put_value("printer_processor.photograph_print", str(self._photograph_print))

    def _load_config(self):
        self._photograph_print = self._config_manager.get_value("printer_processor.photograph_print") == "True"

    def process_text(self, text_msg, wxauto_client):
        """
        处理文本消息 - 实现BaseProcessor接口
        
        Args:
            text_msg (dict): 文本消息数据
            wxauto_client: wxauto客户端实例
            
        Returns:
            bool: 处理成功返回True，失败返回False
        """
        chat_name = text_msg.get("chat_name")
        text_content = text_msg.get("text_content")
        chat_type = text_msg.get("chat_type")
            
        if chat_type == "group":
            if not "@呼噜一号" in text_content:
                logger.info(f"text message from {chat_name}, not @bot skipping")
                return False
        
        #去掉 @呼噜一号，再去除头尾的空格
        text_content = text_content.replace("@呼噜一号", "")
        text_content = text_content.strip()

        if text_content == "开启照片打印功能":
            self._photograph_print = True
            self._save_config()
            wxauto_client.send_text_message(who=chat_name, msg=f"照片打印功能已开启")
            return True
        elif text_content == "关闭照片打印功能":
            self._photograph_print = False
            self._save_config()
            wxauto_client.send_text_message(who=chat_name, msg=f"照片打印功能已关闭")
            return True
        elif text_content == "显示配置":
            wxauto_client.send_text_message(who=chat_name, msg=f"当前打印功能状态: {self._photograph_print}")
            return True

        return False
        
    def process_image(self, image_msg, wxauto_client):
        """
        处理图片消息 - 实现BaseProcessor接口
        
        Args:
            image_msg (dict): 图片消息数据
            wxauto_client: wxauto客户端实例
            
        Returns:
            bool: 处理成功返回True，失败返回False
        """
        try:
            chat_name = image_msg.get("chat_name")
            file_name = image_msg.get("file_name")
            file_id = image_msg.get("file_id")

            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, file_name)
            binarize_file_path = os.path.join(temp_dir, "binarize_" + file_name)

            download_ret = wxauto_client.download_file(file_id, file_path)
            
            #{"success": False, "error": error_msg}
            if not download_ret.get('success'):
                logger.error(f"Download failed for {file_path}: {download_ret.get('error')}")
                self._send_error_response(wxauto_client, chat_name, f"图片下载失败: {download_ret.get('error', '未知错误')}")
                return False
            
            logger.info(f"PrintProcessor processing image from {chat_name}: {file_path}")

            if self._photograph_print:
                image_binarize = ImageBinarrize()
                image_binarize.process_image(input_path=file_path, output_path=binarize_file_path)
            else:
                shutil.copy(file_path, binarize_file_path)

            logger.info(f"PrintProcessor processing image binarize {chat_name}: {binarize_file_path}")

            pdf_path = self._converter.convert_image_to_pdf(binarize_file_path, output_dir=temp_dir)

            ret, job_id = self._printer.print_pdf(pdf_path)

            if ret:
                wxauto_client.send_text_message(who=chat_name, msg=f"已创建打印任务{job_id}")
                logger.info(f"Successfully sent print job {job_id} for {pdf_path}")

                # 启动线程监控打印状态
                self._start_print_job_monitor(job_id, chat_name, temp_dir, file_name, wxauto_client)

                return True
            else:
                error_msg = f"打印失败，请检查打印机设置"
                self._send_error_response(wxauto_client, chat_name, error_msg)
                return False
                            
        except Exception as e:
            logger.error(f"Error processing printer image: {str(e)}")
            self._send_error_response(wxauto_client, image_msg.get("chat_name"), f"处理图片时发生错误: {str(e)}")
            return False
      
    def is_supported_file(self, extension: str) -> bool:
        if extension == '.doc':
            return True
        elif extension == '.docx':
            return True
        elif extension == '.pdf':
            return True
        elif extension == '.wps':
            return True
        else:
            return False
        
    def process_file(self, file_msg, wxauto_client):
        """
        处理文件消息 - 实现BaseProcessor接口
        
        Args:
            file_msg (dict): 文件消息数据
            wxauto_client: wxauto客户端实例
            
        Returns:
            bool: 处理成功返回True，失败返回False
        """
        try:
            chat_name = file_msg.get("chat_name")
            file_name = file_msg.get("file_name")
            file_id = file_msg.get("file_id")

            name, ext = os.path.splitext(file_name)
            
            if not self.is_supported_file(ext):
                error_msg = f"无法识别文件格式，无法打印"
                self._send_error_response(wxauto_client, chat_name, error_msg)
                return False

            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, file_name)

            download_ret = wxauto_client.download_file(file_id, file_path)
            
            #{"success": False, "error": error_msg}
            if not download_ret.get('success'):
                logger.error(f"Download failed for {file_path}: {download_ret.get('error')}")
                self._send_error_response(wxauto_client, chat_name, f"图片下载失败: {download_ret.get('error', '未知错误')}")
                return False
            
            logger.info(f"PrintProcessor processing file from {chat_name}: {file_path}")

            if ext != ".pdf":         
                pdf_path = self._converter.convert_document_to_pdf(file_path, output_dir=temp_dir)
            else:
                pdf_path = file_path
                
            # 直接打印接收到的文件
            ret, job_id = self._printer.print_pdf(pdf_path)

            if ret:
                wxauto_client.send_text_message(who=chat_name, msg=f"已创建打印任务{job_id}")
                logger.info(f"Successfully sent print job {job_id} for {pdf_path}")

                # 启动线程监控打印状态
                self._start_print_job_monitor(job_id, chat_name, temp_dir, file_name, wxauto_client)

                return True
            else:
                error_msg = f"打印失败，请检查打印机设置"
                self._send_error_response(wxauto_client, chat_name, error_msg)
                return False
                            
        except Exception as e:
            logger.error(f"Error processing printer file: {str(e)}")
            self._send_error_response(wxauto_client, file_msg.get("chat_name"), f"处理文件时发生错误: {str(e)}")
            return False

    def _send_error_response(self, wxauto_client, chat_name, error_message):
        """
        发送错误响应
        
        Args:
            wxauto_client: wxauto客户端实例
            chat_name (str): 聊天名称
            error_message (str): 错误消息
        """
        if wxauto_client and chat_name:
            try:
                wxauto_client.send_text_message(who=chat_name, msg=error_message)
            except Exception as e:
                logger.error(f"Failed to send error response: {str(e)}")
  
    def _start_print_job_monitor(self, job_id, chat_name, temp_dir, file_name, wxauto_client):
        """
        启动打印任务状态监控线程
        """
        def monitor_print_job():
            """
            监控打印任务状态的线程函数
            """
            logger.info(f"Starting monitor for print job {job_id}")
            
            completed_states = ['completed', 'canceled', 'aborted']
            max_checks = 100  # 最多检查100次（5分钟）
            
            for i in range(max_checks):
                try:
                    # 检查任务状态
                    status_info = self._printer.get_job_status(job_id)
                    
                    current_state = status_info.get('state_name', 'unknown')
                    
                    # 检查是否完成
                    if current_state in completed_states:
                        if current_state == 'completed':
                            wxauto_client.send_text_message(who=chat_name, msg=f"✅ 打印任务{job_id}, {file_name} 已打印完成")
                            logger.info(f"Print job {job_id} completed successfully")
                        else:
                            wxauto_client.send_text_message(who=chat_name, msg=f"❌ 打印任务{job_id}, {file_name} 打印失败, 当前状态{current_state}")
                            logger.warning(f"Print job {job_id} ended with state: {current_state}")
                        break
                    
                    # 每3秒检查一次
                    time.sleep(3)
                    
                except Exception as e:
                    logger.error(f"Error monitoring print job {job_id}: {str(e)}")
                    time.sleep(3)  # 出错也等待3秒再试
            
            else:
                # 循环正常结束（未break），说明超时了
                wxauto_client.send_text_message(who=chat_name, msg="打印任务监控超时，请手动检查打印机状态")
                logger.warning(f"Print job {job_id} monitoring timeout")

             # 确保清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")
                    
            logger.info(f"Stopped monitoring print job {job_id}")
        
        # 启动监控线程
        monitor_thread = threading.Thread(
            target=monitor_print_job,
            daemon=True,  # 设置为守护线程，主程序退出时自动结束
            name=f"PrintMonitor-{job_id}"
        )
        monitor_thread.start()
        logger.info(f"Started print job monitor thread for job {job_id}")