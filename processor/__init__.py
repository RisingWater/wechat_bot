# processor/__init__.py
"""
Processor package for handling different types of messages
"""

from .homework_processor import HomeworkProcessor
from .chat_processor import ChatProcessor
from .print_processor import PrintProcessor
from .mitv_processor import MitvProcessor
from .license_processor import LicenseProcessor

__all__ = [
    'HomeworkProcessor',
    'ChatProcessor', 
    'PrintProcessor',
    'MitvProcessor',
    'LicenseProcessor'
]