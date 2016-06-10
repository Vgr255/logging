#!/usr/bin/env python3

"""Various types for general and specific uses."""

__all__ = ["NoValue"]

from .decorators import Singleton

@Singleton
class NoValue:
    """Express the lack of value, as None has a special meaning."""

    def __repr__(self):
        """Return the explicit NoValue string."""
        return "NoValue"

    def __bool__(self):
        """Return False no matter what."""
        return False
