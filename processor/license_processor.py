# license_processor.py
import logging
import os
import subprocess
import tempfile
import shutil
from wxauto import WXAuto

logger = logging.getLogger(__name__)

class LicenseProcessor:
    def __init__(self, env_file=".env"):
        self.wxauto_client = WXAuto(env_file)
        self.processor_name = "license_processor"
        logger.info(f"LicenseProcessor initialized")
    
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
            # 使用传入的wxauto_client或内置的
            client = wxauto_client if wxauto_client else self.wxauto_client
            
            chat_name = file_msg.get("chat_name")
            file_path = file_msg.get("file_path")
            
            logger.info(f"LicenseProcessor processing file from {chat_name}: {file_path}")

            basename = os.path.basename(file_path)  # 获取文件名
            name, ext = os.path.splitext(basename)

            output_dir = os.path.dirname(file_path)

            # 检查文件扩展名
            if ext.lower() != '.ctr':
                error_msg = f"不支持的文件格式 '{ext}'，仅支持 .ctr 文件"
                self._send_error_response(client, chat_name, error_msg)
                return False

            # 验证文件存在
            if not os.path.exists(file_path):
                error_msg = f"文件不存在: {basename}"
                self._send_error_response(client, chat_name, error_msg)
                return False
                
            # 生成输出文件名
            output_filename = name + '.ctl'
            ctl_path = os.path.join(output_dir, output_filename)
                
            # 调用转换工具
            logger.info(f"Converting {basename} to {output_filename}")
            conversion_success = self._convert_ctr_to_ctl(file_path, ctl_path)
                
            if not conversion_success:
                error_msg = f"文件转换失败: {basename}"
                self._send_error_response(client, chat_name, error_msg)
                return False
            
            # 验证生成的ctl文件
            if not os.path.exists(ctl_path):
                error_msg = f"转换后的文件未生成: {output_filename}"
                self._send_error_response(client, chat_name, error_msg)
                return False
            
            file_size = os.path.getsize(ctl_path)
            if file_size == 0:
                error_msg = f"转换后的文件为空: {output_filename}"
                self._send_error_response(client, chat_name, error_msg)
                return False
            
            # 发送转换成功的消息
            client.send_text_message(
                who=chat_name, 
                msg=f"✅ 文件转换成功，正在发送 {output_filename}..."
            )
                
            # 发送转换后的文件
            send_result = client.send_file_message(
                who=chat_name,
                file_path=ctl_path,
                exact=True,
                description=f"由 {basename} 转换生成的许可证文件",
                uploader="license_processor"
            )
                
            if send_result.get("success"):
                logger.info(f"Successfully sent converted file {output_filename} to {chat_name}")
                client.send_text_message(
                    who=chat_name, 
                    msg=f"📤 文件发送完成: {output_filename}"
                )
                return True
            else:
                error_msg = f"文件发送失败: {send_result.get('error', '未知错误')}"
                self._send_error_response(client, chat_name, error_msg)
                return False
                            
        except Exception as e:
            logger.error(f"Error processing license file: {str(e)}")
            error_msg = f"处理许可证文件时发生错误: {str(e)}"
            self._send_error_response(
                wxauto_client if wxauto_client else self.wxauto_client, 
                file_msg.get("chat_name"), 
                error_msg
            )
            return False

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
            # 构建命令
            cmd = [
                '/workdir/ctr2ctl',
                '--input', input_path,
                '--output', output_path
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
def main():
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing LicenseProcessor class...")
    
    # 创建处理器实例
    processor = LicenseProcessor()
    
    # 测试文件支持检查
    print("\nTesting file support check...")
    print(f"Support .ctr: {processor.is_supported_file('.ctr')}")
    print(f"Support .txt: {processor.is_supported_file('.txt')}")
    print(f"Support .CTR: {processor.is_supported_file('.CTR')}")

if __name__ == "__main__":
    main()