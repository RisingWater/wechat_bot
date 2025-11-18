# device/__init__.py
"""
Processor package for handling different types of messages
"""

from .baidu_ocr import BaiduOCR
from .deepseek import DeepSeekAPI
from .wxauto import WXAuto
from .amap import AmapAPI
from .tencent_stock import TencentStockAPI
from .open_door import OpenDoorAPI
from .dsmxp import DSMSmartDoorAPI

__all__ = [
    'BaiduOCR',
    'DeepSeekAPI',
    'WXAuto',
    'AmapAPI',
    'TencentStockAPI',
    'OpenDoorAPI',
    'DSMSmartDoorAPI',
]