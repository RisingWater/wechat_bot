# processor/__init__.py
"""
Processor package for handling different types of messages
"""

import sys

from .homework_processor import HomeworkProcessor
from .chat_processor import ChatProcessor
from .location_processor import LocationProcessor

if not sys.platform == "win32":
    from .print_processor import PrintProcessor
    from .mitv_processor import MitvProcessor
    from .license_processor import LicenseProcessor

if not sys.platform == "win32":
    __all__ = [
        'HomeworkProcessor',
        'ChatProcessor', 
        'LocationProcessor'
        'PrintProcessor',
        'MitvProcessor',
        'LicenseProcessor',
    ]
else:
    __all__ = [
        'HomeworkProcessor',
        'ChatProcessor', 
        'LocationProcessor'
    ]