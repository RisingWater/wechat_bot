# device/__init__.py
"""
Processor package for handling different types of messages
"""

import sys
import logging

logger = logging.getLogger(__name__)

from .coord_transfrom import CoordTransform
from .qb_location import QBLocation

# 尝试导入平台特定模块，如果失败则记录警告但不阻止其他导入
if not sys.platform == "win32":
    try:
        from .print import Printer
        from .mitv import MiTV
        HAS_PLATFORM_MODULES = True
    except ImportError as e:
        logger.warning(f"无法导入平台特定模块: {e}")
        HAS_PLATFORM_MODULES = False
        Printer = None
        MiTV = None
else:
    HAS_PLATFORM_MODULES = False
    Printer = None
    MiTV = None

if not sys.platform == "win32" and HAS_PLATFORM_MODULES:
    __all__ = [
        'MiTV',
        'Printer',
        'QBLocation',
        'CoordTransform'
    ]
else:
    __all__ = [
        'QBLocation',
        'CoordTransform'
    ]