# device/__init__.py
"""
Processor package for handling different types of messages
"""

import sys

from .coord_transfrom import CoordTransform
from .qb_location import QBLocation

if not sys.platform == "win32":
    from .print import Printer
    from .mitv import MiTV

if not sys.platform == "win32":
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