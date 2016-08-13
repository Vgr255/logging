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

    super() -> same as super(__class__, <first argument>)
    super(class) -> unbound super object (see below for more information)
    super(class, instance) -> bound instance super object; see below
    super(class, subclass) -> bound class super object; see below

    The no-argument form of super will return one of the two bound
    versions, or raise an error if it's unable to do so.

    This is typically used with single and multiple inheritence, as in:

    class B(A):
        def instance_method(self, arg):
            super().instance_method(arg)

    This also works for class methods:

    class C(A):
        @classmethod
        def class_method(cls, arg):
            super().class_method(arg)

    An unbound super object is an object which knows the class that it
    is defined for, but doesn't have a reference to any instance. It is
    usually defined as a class attribute. Accessing the class attribute
    from the instance will return a new object, which will be bound to
    the instance. That object will be bound, and will behave the same
    as if it had been defined on the instance. This behaviour is the
    same as the built-in super. Furthermore, this version will also
    return a new, bound object on access from a class. This is useful
    if used in a class method (as above)

    Bound objects, on the other hand, contain a reference to the class
    they were defined in, as well as to the instance or subclass

    Note: to use the zero-argument version of super, it needs to be
    bound to the name 'super'; for example this won't work:

        from logger.types import super as custom_super

        class D(A):
            def instance_method(self):
                custom_super().instance_method()

    Do note that the built-in super suffers from the same caveat! So,
    for instance, the following will not work, either:

        builtin_super = super

        class E(A):
            def instance_method(self):
                builtin_super().instance_method()

    This is due to the fact that Python (actually, CPython) adds a
    '__class__' cell to the function whenever it sees the name 'super'
    in the scope (other than it being assigned to). So keeping this as
    'super' effectively makes the compiler do the work for us, freely!

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
