# homework.py
import logging
import json
import uuid
import os
import shutil
from utils.file_converter import FileConverter
from utils.file_recognize import FileRecognizer
from device.print import Printer

logger = logging.getLogger(__name__)

class PrintProcessor:
    def __init__(self, env_file=".env"):
        self._converter = FileConverter()
        self._printer = Printer(env_file)
        self._file_recognize = FileRecognizer()
        self.processor_name = "print_processor"
        logger.info(f"PrintProcessor initialized")
    
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
            file_path = image_msg.get("file_path")
            
            logger.info(f"PrintProcessor processing image from {chat_name}: {file_path}")

            # 获取file_path的文件夹路径作为输出目录
            output_dir = os.path.dirname(file_path) + "/converted_pdfs"
            os.makedirs(output_dir, exist_ok=True)

            pdf_path = self._converter.convert_image_to_pdf(file_path, output_dir=output_dir)

            ret, job_id = self._printer.print_pdf(pdf_path)

            if ret:
                wxauto_client.send_text_message(who=chat_name, msg=f"已创建打印任务{job_id}")
                logger.info(f"Successfully sent print job {job_id} for {pdf_path}")

                # 启动线程监控打印状态
                self._start_print_job_monitor(job_id, chat_name, pdf_path, wxauto_client)

                return True
            else:
                error_msg = f"打印失败，请检查打印机设置"
                self._send_error_response(wxauto_client, chat_name, error_msg)
                return False
                            
        except Exception as e:
            logger.error(f"Error processing printer image: {str(e)}")
            self._send_error_response(wxauto_client, image_msg.get("chat_name"), f"处理图片时发生错误: {str(e)}")
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
            file_path = file_msg.get("file_path")
            
            logger.info(f"PrintProcessor processing file from {chat_name}: {file_path}")

            extension = self._file_recognize.get_extension(file_path)

            if extension == ".unknown":
                error_msg = f"无法识别文件格式，无法打印"
                self._send_error_response(wxauto_client, chat_name, error_msg)
                return False

            output_dir = os.path.dirname(file_path) + "/converted_pdfs"
            os.makedirs(output_dir, exist_ok=True)

            new_filepath = output_dir + "/" + str(uuid.uuid4()) + extension
            shutil.move(file_path, new_filepath)
            file_path = new_filepath

            if extension != ".pdf":         
                pdf_path = self._converter.convert_document_to_pdf(file_path, output_dir=output_dir)
            else:
                pdf_path = file_path
                
            # 直接打印接收到的文件
            ret, job_id = self._printer.print_pdf(pdf_path)

            if ret:
                wxauto_client.send_text_message(who=chat_name, msg=f"已创建打印任务{job_id}")
                logger.info(f"Successfully sent print job {job_id} for {pdf_path}")

                # 启动线程监控打印状态
                self._start_print_job_monitor(job_id, chat_name, pdf_path, wxauto_client)

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
  
    def _start_print_job_monitor(self, job_id, chat_name, file_path, wxauto_client):
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
                            wxauto_client.send_text_message(who=chat_name, msg=f"✅ 打印任务{job_id}, 已完成")
                            logger.info(f"Print job {job_id} completed successfully")
                        else:
                            wxauto_client.send_text_message(who=chat_name, msg=f"❌ 打印任务{job_id}, 失败, 当前状态{current_state}")
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
            
            logger.info(f"Stopped monitoring print job {job_id}")
        
        # 启动监控线程
        monitor_thread = threading.Thread(
            target=monitor_print_job,
            daemon=True,  # 设置为守护线程，主程序退出时自动结束
            name=f"PrintMonitor-{job_id}"
        )
        monitor_thread.start()
        logger.info(f"Started print job monitor thread for job {job_id}")