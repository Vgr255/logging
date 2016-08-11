#!/usr/bin/env python3

"""Various types for general and specific uses."""

__all__ = ["NoValue"]

import sys

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

class super:
    """Improved version of the built-in super() with some additions.

    This supports every feature that the built-in version supports, but
    is more robust and handles more cases than the built-in version.

    Note: to use the zero-argument version of 'super', it needs to
    actually be bound to the name 'super'; i.e. this won't work:

        from logger.types import super as custom_super

        class Foo:
            def bar(self):
                custom_super().bar()

    Do note that the built-in 'super' suffers from the same caveat! So,
    for instance, the following will not work, either:

        builtin_super = super

        class Bar:
            def baz(self):
                builtin_super().baz()

    This is due to the fact that Python (actually, CPython) adds a
    '__class__' cell to the function when it sees the name 'super'
    being called with no arguments. Rebinding the name within the local
    scope is fine, as long as Python sees that the global name 'super'
    is being called.

    """

    __slots__ = "__self__", "__self_class__", "__thisclass__"

    def __init__(self, owner_class=None, object=None):
        """Create a new bound or unbound super object."""

        if owner_class is None and object is None:
            try:
                frame = sys._getframe()
            except AttributeError:
                frame = None

            if frame is not None:
                frame = frame.f_back

            if frame is None:
                raise RuntimeError("super(): no current frame")

            code = frame.f_code

            if code is None:
                raise RuntimeError("super(): no code object")

            if code.co_argcount == 0:
                raise RuntimeError("super(): no arguments")

            if code.co_varnames[0] not in frame.f_locals:
                raise RuntimeError("super(): arg[0] deleted")

            # TODO: pretty much everything
