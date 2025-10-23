# license_processor.py
import logging
import os
import subprocess
import shutil
import tempfile

logger = logging.getLogger(__name__)

class LicenseProcessor:
    def __init__(self, env_file=".env"):
        self.processor_name = "license_processor"
        logger.info(f"LicenseProcessor initialized")

    def description(self) -> str:
        return "融易云授权处理器"
    
    def process_file(self, file_msg, wxauto_client=None):
        """
        处理文件消息 - 实现BaseProcessor接口
        
        Args:
            file_msg (dict): 文件消息数据
            wxauto_client: wxauto客户端实例（如果为None则使用内置的）
            
        Returns:
            bool: 处理成功返回True，失败返回False
        """
        try:
            chat_name = file_msg.get("chat_name")
            ctr_name = file_msg.get("file_name")
            file_id = file_msg.get("file_id")
            
            name, ext = os.path.splitext(ctr_name)
             # 检查文件扩展名
            if ext.lower() != '.ctr':
                error_msg = f"不支持的文件格式 '{ext}'，仅支持 .ctr 文件"
                self._send_error_response(wxauto_client, chat_name, error_msg)
                return False

            temp_dir = tempfile.mkdtemp()
            ctr_path = os.path.join(temp_dir, ctr_name)

            ctl_name = name + '.ctl'
            ctl_path = os.path.join(temp_dir, ctl_name)

            download_ret = wxauto_client.download_file(file_id, ctr_path)

            #{"success": False, "error": error_msg}
            if not download_ret.get('success'):
                logger.error(f"Download failed for {ctr_path}: {download_ret.get('error')}")
                self._send_error_response(wxauto_client, chat_name, f"图片下载失败: {download_ret.get('error', '未知错误')}")
                return False
            
            logger.info(f"LicenseProcessor processing file from {chat_name}: {ctr_path}")
                
            # 调用转换工具
            logger.info(f"Converting {ctr_name} to {ctl_name}")
            conversion_success = self._convert_ctr_to_ctl(ctr_path, ctl_path)
                
            if not conversion_success:
                error_msg = f"文件转换失败: {ctr_name}"
                self._send_error_response(wxauto_client, chat_name, error_msg)
                return False
            
            # 验证生成的ctl文件
            if not os.path.exists(ctl_path):
                error_msg = f"转换后的文件未生成: {ctl_name}"
                self._send_error_response(wxauto_client, chat_name, error_msg)
                return False
            
            file_size = os.path.getsize(ctl_path)
            if file_size == 0:
                error_msg = f"转换后的文件为空: {ctl_name}"
                self._send_error_response(wxauto_client, chat_name, error_msg)
                return False
            
            # 发送转换成功的消息
            wxauto_client.send_text_message(
                who=chat_name, 
                msg=f"✅ 文件转换成功，正在发送 {ctl_name}..."
            )
                
            # 发送转换后的文件
            send_result = wxauto_client.send_file_message(
                who=chat_name,
                file_path=ctl_path,
                exact=True,
                description=f"由 {ctr_name} 转换生成的许可证文件",
                uploader="license_processor"
            )
                
            if send_result.get("success"):
                logger.info(f"Successfully sent converted file {ctl_name} to {chat_name}")
                wxauto_client.send_text_message(
                    who=chat_name, 
                    msg=f"📤 文件发送完成: {ctl_name}"
                )
                return True
            else:
                error_msg = f"文件发送失败: {send_result.get('error', '未知错误')}"
                self._send_error_response(wxauto_client, chat_name, error_msg)
                return False
                            
        except Exception as e:
            logger.error(f"Error processing license file: {str(e)}")
            error_msg = f"处理许可证文件时发生错误: {str(e)}"
            self._send_error_response(
                wxauto_client, 
                file_msg.get("chat_name"), 
                error_msg
            )
            return False

        finally:
            # 确保清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")

    def _convert_ctr_to_ctl(self, input_path, output_path):
        """
        调用ctr2ctl工具进行文件转换
        
        Args:
            input_path (str): 输入的.ctr文件路径
            output_path (str): 输出的.ctl文件路径
            
        Returns:
            bool: 转换成功返回True，失败返回False
        """
        try:
            input_path_str = str(input_path)
            output_path_str = str(output_path)
            # 构建命令
            cmd = [
                '/workdir/ctr2ctl',
                '--input', input_path_str,
                '--output', output_path_str
            ]
            
            logger.info(f"Executing command: {' '.join(cmd)}")
            
            # 执行转换命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30秒超时
            )
            
            # 检查执行结果
            if result.returncode == 0:
                logger.info(f"Conversion successful: {input_path} -> {output_path}")
                if result.stdout:
                    logger.info(f"Conversion stdout: {result.stdout}")
                return True
            else:
                logger.error(f"Conversion failed with return code {result.returncode}")
                if result.stderr:
                    logger.error(f"Conversion stderr: {result.stderr}")
                if result.stdout:
                    logger.error(f"Conversion stdout: {result.stdout}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Conversion timeout: {input_path}")
            return False
        except FileNotFoundError:
            logger.error("ctr2ctl tool not found. Please ensure './ctr2ctl' is in the current directory.")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during conversion: {str(e)}")
            return False

    def is_supported_file(self, extension: str) -> bool:
        """
        检查是否支持该文件类型
        
        Args:
            extension (str): 文件扩展名
            
        Returns:
            bool: 支持返回True，否则返回False
        """
        return extension.lower() == '.ctr'

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
                wxauto_client.send_text_message(
                    who=chat_name, 
                    msg=f"❌ {error_message}"
                )
            except Exception as e:
                logger.error(f"Failed to send error response: {str(e)}")

    def cleanup(self):
        """
        清理资源
        """
        logger.info("LicenseProcessor cleanup completed")


# 测试函数
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger.info("Testing LicenseProcessor class...")
    
    # 创建处理器实例
    processor = LicenseProcessor()
    
    # 测试文件支持检查
    logger.info("\nTesting file support check...")
    logger.info(f"Support .ctr: {processor.is_supported_file('.ctr')}")
    logger.info(f"Support .txt: {processor.is_supported_file('.txt')}")
    logger.info(f"Support .CTR: {processor.is_supported_file('.CTR')}")

if __name__ == "__main__":
    main()