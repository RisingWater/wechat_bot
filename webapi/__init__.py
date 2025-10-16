# device/__init__.py
"""
Processor package for handling different types of messages
"""

from .baidu_ocr import BaiduOCR
from .deepseek import DeepSeekAPI
from .wxauto import WXAuto

__all__ = [
    'BaiduOCR',
    'DeepSeekAPI',
    'WXAuto'
]