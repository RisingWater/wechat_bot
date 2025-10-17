import subprocess
import os
import logging
import img2pdf
from pathlib import Path

class FileConverter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def convert_image_to_pdf(self, input_name: str, output_dir: str) -> str:
        """
        将图片转换为PDF
        
        Args:
            input_name: 输入图片路径
            output_dir: 输出PDF路径
            
        Returns:
            生成的PDF文件路径
        """
        if not os.path.exists(input_name):
            raise FileNotFoundError(f"输入图片不存在: {input_name}")

        if output_dir is None:
            output_dir = os.path.dirname(input_file)

        input_name = Path(input_file).stem
        output_file = os.path.join(output_dir, f"{input_name}.pdf")
        
        try:
            with open(output_file, "wb") as f:
                f.write(img2pdf.convert(input_name))
            self.logger.info(f"图片转换成功: {input_name} -> {output_file}")
            return output_file
        except Exception as e:
            self.logger.error(f"图片转换失败: {str(e)}")
            raise
    
    def convert_document_to_pdf(self, input_file: str, output_dir: str = None) -> str:
        """
        将文档转换为PDF
        
        Args:
            input_file: 输入文件路径
            output_dir: 输出目录，默认为输入文件所在目录
            
        Returns:
            生成的PDF文件路径
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"输入文件不存在: {input_file}")
        
        if output_dir is None:
            output_dir = os.path.dirname(input_file)
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成输出文件名
        input_name = Path(input_file).stem
        output_file = os.path.join(output_dir, f"{input_name}.pdf")
        
        try:
            # 使用LibreOffice进行转换
            cmd = [
                'libreoffice', '--headless', '--convert-to', 'pdf:writer_pdf_Export',
                '--outdir', output_dir, input_file
            ]
            
            self.logger.info(f"执行转换命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                self.logger.info(f"转换成功: {input_file} -> {output_file}")
                return output_file
            else:
                self.logger.error(f"转换失败: {result.stderr}")
                raise Exception(f"文档转换失败: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"转换超时: {input_file}")
            raise Exception("文档转换超时")
        except Exception as e:
            self.logger.error(f"转换异常: {str(e)}")
            raise

# 使用示例
def main():
    converter = DocumentConverter()
    
    # 转换单个文件
    try:
        test_files = [
            "test1.doc",
            "test2.docx",
            "test3.wps"
        ]

        output_dir = "/root/converted_pdfs/"

        for file in test_files:
            pdf_path = converter.convert_to_pdf(file, output_dir=output_dir)

        test_images = [
            "image1.jpg",
            "image2.png"
        ]   

        for img in test_images:
            pdf_path = converter.convert_image_to_pdf(img, output_dir=output_dir)

        print(f"转换完成: {pdf_path}")
    except Exception as e:
        print(f"转换失败: {e}")