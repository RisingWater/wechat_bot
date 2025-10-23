#!/usr/bin/env python3
"""
文件格式识别工具
识别PDF、DOC、DOCX、WPS文件格式
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class FileRecognizer:
    """
    文件格式识别器
    通过二进制内容识别PDF、DOC、DOCX、WPS文件
    """
    
    def __init__(self):
        """初始化文件识别器"""
    
    def _read_file_header(self, file_path: str, bytes_to_read: int = 16) -> Optional[bytes]:
        """
        读取文件头部内容
        
        Args:
            file_path (str): 文件路径
            bytes_to_read (int): 要读取的字节数
            
        Returns:
            Optional[bytes]: 文件头部字节数据，读取失败返回None
        """
        try:
            with open(file_path, 'rb') as file:
                return file.read(bytes_to_read)
        except Exception as e:
            logger.error(f"读取文件头失败 {file_path}: {e}")
            return None
    
    def _is_pdf(self, file_path: str) -> bool:
        """
        检查文件是否为PDF格式
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            bool: 如果是PDF返回True，否则返回False
        """
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {file_path}")
            return False
        
        header = self._read_file_header(file_path, 8)
        if header is None:
            return False
        
        # PDF文件签名检查
        if header.startswith(b'%PDF-'):
            logger.info(f"文件 {file_path} 是PDF格式")
            return True
        
        # 处理可能包含换行符的PDF文件
        if b'\n%PDF-' in header or b'\r%PDF-' in header:
            logger.info(f"文件 {file_path} 是PDF格式（含换行符）")
            return True
        
        logger.debug(f"文件 {file_path} 不是PDF格式")
        return False
    
    def _is_doc(self, file_path: str) -> bool:
        """
        检查文件是否为DOC格式（Microsoft Word 97-2003）
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            bool: 如果是DOC返回True，否则返回False
        """
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {file_path}")
            return False
        
        header = self._read_file_header(file_path, 8)
        if header is None:
            return False
        
        # DOC文件签名：D0 CF 11 E0 A1 B1 1A E1 (Microsoft Compound File)
        if header.startswith(b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'):
            logger.info(f"文件 {file_path} 是DOC格式")
            return True
        
        logger.debug(f"文件 {file_path} 不是DOC格式")
        return False
    
    def _is_docx(self, file_path: str) -> bool:
        """
        检查文件是否为DOCX格式（Microsoft Word 2007+）
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            bool: 如果是DOCX返回True，否则返回False
        """
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {file_path}")
            return False
        
        header = self._read_file_header(file_path, 4)
        if header is None:
            return False
        
        # DOCX文件签名：PK开头（ZIP格式）
        if header.startswith(b'PK\x03\x04'):
            # 进一步检查是否为Office文档
            try:
                with open(file_path, 'rb') as file:
                    # 读取更多数据来确认包含Word文档结构
                    data = file.read(2000)
                    # 检查是否包含Word特定的文件结构
                    if b'word/' in data or b'[Content_Types].xml' in data:
                        logger.info(f"文件 {file_path} 是DOCX格式")
                        return True
            except Exception as e:
                logger.error(f"检查DOCX文件失败 {file_path}: {e}")
        
        logger.debug(f"文件 {file_path} 不是DOCX格式")
        return False
    
    def _is_wps(self, file_path: str) -> bool:
        """
        检查文件是否为WPS格式（金山WPS文档）
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            bool: 如果是WPS返回True，否则返回False
        """
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {file_path}")
            return False
        
        try:
            with open(file_path, 'rb') as file:
                # 读取文件头进行识别
                header = file.read(32)  # 读取更多字节以包含WPS签名
                
                # WPS文件有特定的文件头签名
                # WPS文字文档: D0 CF 11 E0 A1 B1 1A E1 开头，且在特定偏移处有WPS标识
                if header.startswith(b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'):
                    # 在Compound File中查找WPS特定标识
                    # WPS文件在特定位置包含"WPS Office"或"Kingsoft WPS"等标识
                    file.seek(0)
                    full_data = file.read(4096)  # 读取更多数据来查找WPS标识
                    
                    # 查找WPS特定的标识字符串
                    wps_identifiers = [
                        b'WPS Office',
                        b'Kingsoft WPS', 
                        b'Kingsoft Office',
                        b'WPSWriter',
                        b'WPSPresentation',
                        b'WPSSpreadsheets'
                    ]
                    
                    for identifier in wps_identifiers:
                        if identifier in full_data:
                            logger.info(f"文件 {file_path} 是WPS格式 (标识: {identifier})")
                            return True
                    
                    # 检查文件扩展名作为辅助判断（如果文件有扩展名）
                    _, ext = os.path.splitext(file_path)
                    if ext.lower() in ['.wps', '.et', '.dps']:
                        logger.info(f"文件 {file_path} 可能是WPS格式 (基于扩展名)")
                        return True
                
                # 新的WPS文件格式（基于XML的）
                elif header.startswith(b'PK\x03\x04'):
                    # 检查是否为WPS Office 2019+ 格式
                    file.seek(0)
                    full_data = file.read(8192)
                    
                    # 在ZIP包中查找WPS特定的文件结构
                    if (b'wps.xml' in full_data or 
                        b'wpsDocument.xml' in full_data or
                        b'WPSDocument' in full_data):
                        logger.info(f"文件 {file_path} 是WPS格式 (新版XML格式)")
                        return True
            
            logger.debug(f"文件 {file_path} 不是WPS格式")
            return False
            
        except Exception as e:
            logger.error(f"检查WPS文件失败 {file_path}: {e}")
            return False

    def get_extension(self, file_path: str) -> str:
        """
        根据文件内容识别文件类型并返回对应的扩展名字符串
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            str: 文件扩展名（如：'.pdf', '.doc', '.docx', '.wps'），未知返回'.unknown'
        """
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {file_path}")
            return '.unknown'
        
        # 按优先级检查文件类型
        if self._is_pdf(file_path):
            return '.pdf'
        elif self._is_docx(file_path):
            return '.docx'
        elif self._is_wps(file_path):
            return '.wps'
        elif self._is_doc(file_path):
            return '.doc'
        else:
            logger.info(f"文件 {file_path} 类型未知")
            return '.unknown'


# 使用示例
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # 创建识别器实例
    recognizer = FileRecognizer()
    
    # 测试文件列表（请替换为实际文件路径）
    test_files = [
        "example.pdf",
        "example.doc", 
        "example.docx",
        "example.wps",
        "unknown_file"
    ]
    
    logger.info("文件格式识别测试")
    logger.info("=" * 50)
    
    for file_path in test_files:
        if os.path.exists(file_path):
            logger.info(f"\n📄 文件: {file_path}")
            logger.info(f"🔍 检测结果:")
            logger.info(f"   推荐扩展名: {recognizer.get_extension(file_path)}")
        else:
            logger.info(f"\n⚠️  文件不存在: {file_path}")