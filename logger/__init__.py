#!/usr/bin/env python3

"""Logging package for specific and general needs.

This exposes all the defined loggers, and a generic ready-to-use Logger
for general needs, which can be used right away.

"""

__author__ = "Emanuel 'Vgr' Barry"

__version__ = "0.2.3"
__status__ = "Mass Refactor [Unstable]"

__all__ = ["loggers"]

from . import loggers

from .loggers import *

__all__.extend(loggers.__all__)
