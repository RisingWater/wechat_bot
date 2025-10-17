# processor/__init__.py
"""
Processor package for handling different types of messages
"""

from .homework_processor import HomeworkProcessor
from .chat_processor import ChatProcessor
from .print_processor import PrintProcessor
from .cmd_processor import CmdProcessor
#from .license_processor import LicenseProcessor

__all__ = [
    'HomeworkProcessor',
    'ChatProcessor', 
    'PrintProcessor',
    'CmdProcessor'
]