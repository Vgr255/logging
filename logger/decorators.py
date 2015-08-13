#!/usr/bin/env python3

__all__ = ["handle_bypass", "check_bypass", "log_usage", "log_use",
           "total_decorate", "attribute", "Singleton"]

class handle_bypass:
    """Default bypasser handler for methods that do not support it."""

    def __init__(self, func):
        """Create a new bypass handler."""
        self.func = func

    def __get__(self, instance, owner):
        """Access the method through the instance."""
        if instance is None:
            return self
        def handler(*args, **kwargs):
            if not hasattr(instance, "bypassed"):
                instance.bypassed = {}
                try:
                    return self.func(instance, *args, **kwargs)
                finally:
                    del self.bypassed

            return self.func(instance, *args, **kwargs)

        for attr in ("__name__", "__qualname__", "__doc__", "__module__"):
            setattr(handler, attr, getattr(self.func, attr))

        return handler

class check_bypass:
    """Handler to get the proper bypass check decorator."""

    def __init__(self, func):
        """Create the bypass checker."""
        self.func = func

    def __get__(self, instance, owner):
        """Access the method through the instance."""
        if instance is None:
            return self
        def checker(*args, **kwargs):
            if not hasattr(instance, "bypassed"):
                instance.bypassed = {}
                name = "_check_%s_" % owner._bp_handler
                if not hasattr(self, name):
                    raise TypeError("%r does not have a bypass handler" %
                                    owner.__name__)
                try:
                    return getattr(self, name)(instance, *args, **kwargs)
                finally:
                    try:
                        del instance.bypassed
                    except AttributeError:
                        pass # already deleted

            return self.func(instance, *args, **kwargs)

        for attr in ("__name__", "__qualname__", "__doc__", "__module__"):
            setattr(checker, attr, getattr(self.func, attr))

        return checker

    @staticmethod
    def _get_setting(module, attr, catch=False):
        """Get the proper setting from inside a dictionary or module."""
        if module is None:
            return attr
        try:
            value = module[attr]
        except (TypeError, KeyError, IndexError):
            try:
                value = getattr(module, attr)
            except AttributeError:
                if catch:
                    return False
                raise
        return value

    def _check_base_(self, instance, *args, **kwargs):
        """Checker for the base class."""
        for setting, pairs, mod, attr in instance.bypassers.items():
            if mod is NoValue or attr is NoValue:
                continue
            for module, attribute in pairs:
                if self._get_setting(module, attribute, catch=True):
                    instance.bypassed[setting] = self._get_setting(mod, attr)
                    break

        return self.func(instance, *args, **kwargs)

    def _check_type_(self, instance, *args, type=None, file=None, **kwargs):
        """Checker for the type-based loggers."""
        if file is type is None:
            type = "normal"

        if type is None:
            for t, f in instance.logfiles.items():
                if f == file:
                    type = t
                    break
            else:
                type = "normal"

        if file is None:
            file = instance.logfiles.get(type, instance.logfiles["normal"])

        for setting, types, pairs, mod, attr in instance.bypassers.items():
            if mod is NoValue or attr is NoValue:
                continue
            for module, attribute in pairs:
                if self._get_setting(module, attribute, catch=True):
                    instance.bypassed[setting] = self._get_setting(mod, attr)
                    break
            else:
                if type in types:
                    instance.bypassed[setting] = self._get_setting(mod, attr)

        return self.func(instance, *args, type=type, file=file, **kwargs)

    def _check_level_(self, instance, *args, level=None, file=None, **kwargs):
        """Checker for the level-based loggers."""
        if file is None:
            file = instance.default_file
        if level is None:
            level = instance.default_level

class log_usage:
    """Decorator to log function and method usage.

    There are three ways to use this decorator:

    >>> from logger import log_usage
    >>> @log_usage() # @log_usage(None) has the same effect
    ... def foo():
    ...     print("spam")
    ...
    >>> foo()
    Call: __main__.foo()
    spam

    >>> from logger import log_usage, Logger
    >>> handler = Logger()
    >>> @log_usage(handler)
    ... def foo(first, second, third=3, fourth=None):
    ...     print("eggs")
    ...
    >>> foo("bar", 42, 7, fourth=24)
    Call: __main__.foo('bar', 42, 7, fourth=24)
    eggs

    >>> from logger import log_usage, Logger
    >>> handler = Logger()
    >>> args = (42, 1337)
    >>> kwargs = {"foo": 0, "bar": 1}
    >>> def baz(hello, world, foo=7, bar=22):
    ...     print("spam or eggs")
    ...
    >>> log_usage.call(baz, handler, args, kwargs)
    Call: __main__.baz(42, 1337, foo=0, bar=1)
    spam or eggs

    The handler is the logger object that will be used for logging of
    the function and method usage.

    The `call` method is called when this class is used as a decorator,
    and can be called directly as well.

    The following are possible handlers; they are stated by priority
    (so the first handle takes precedence over the second, which takes
    precedence over the third, and so on).

    - A subclass of BaseLogger; an instance of it will be created and
      its 'logger' method will be used.
    - Any instance of BaseLogger or its subclasses; its 'logger' method
      will be used.
    - Any class, they will be instantiated and called directly.
    - Any function or method, they will be called directly.
    - Any instance of any class, they will be called directly.
    - None (or no passed function), BaseLogger's logger will be used

    If none of the above matches for some reason, it will create a new
    instance of BaseLogger and use its 'logger' method.

    It is very easy to subclass this into a decorator that doesn't
    require any parameter. See log_use for an example.

    The class attribute `_default_handler` is a BaseLogger subclass,
    or any class, but it must have a `logger` method.

    """

    _default_handler = None

    def __new__(cls, *args, **kwargs):
        if cls._default_handler is None:
            from .logger import BaseLogger
            cls._default_handler = BaseLogger
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, func=None):
        """Prepare the decorator."""
        from inspect import (

            isclass,
            isroutine,

        )

        if func is None:
            self.handler = self._default_handler().logger
        elif isclass(func) and issubclass(func, self._default_handler):
            self.handler = func().logger
        elif isinstance(func, self._default_handler):
            self.handler = func.logger
        elif isclass(func):
            self.handler = func()
        elif isroutine(func):
            self.handler = func
        else:
            self.handler = self._default_handler().logger

    def __call__(self, func):
        """Call the handler."""
        self.func = func
        return lambda *args, **rest: self.call(func, args, rest, self.handler)

    def __get__(self, instance, owner):
        """Make the decorator work properly on methods."""
        def caller(*args, **kwargs):
            if instance is not None:
                args = (instance,) + args
            return self.call(self.func, args, kwargs, self.handler)

        for attr in ("__name__", "__qualname__", "__doc__", "__module__"):
            if hasattr(self.func, attr):
                setattr(caller, attr, getattr(self.func, attr))
        return caller

    @classmethod
    def call(cls, func, args, kwargs, handler=None):
        """Log usage of a function or method and call it."""

        if handler is None:
            if cls._default_handler is None:
                from .logger import BaseLogger
                cls._default_handler = BaseLogger
            handler = cls._default_handler().logger

        if handler is func:
            raise RuntimeError("cannot decorate the function with itself")

        params = (", ".join(repr(x) for x in args),
                  ", ".join("%s=%r" % (k,v) for k,v in kwargs.items()))

        if all(params):
            params = ", ".join(params)
        else:
            params = "".join(params)

        # regex pattern for translation: r"^Call: .+\..+\(.*\)$"
        handler("Call: %s(%s)" % (func.__qualname__, params))

        return func(*args, **kwargs)

class log_use(log_usage):
    """Usage logging decorator that doesn't require a handler.

    This can be easily subclassed to change the handler used, or simply
    change the handler at runtime.

    """

    def __init__(self, func):
        """Prepare a handler-less decorator."""
        self.handler = self._default_handler().logger
        self.func = func

    def __call__(self, *args, **kwargs):
        """Handle the calling of the function itself."""
        return self.call(self.func, args, kwargs, self.handler)

def total_decorate(cls=None, *, handler=log_use, name=None):
    """Decorate all of the class' methods with `handler`.

    There are three ways to use this class decorator:

    @total_decorate
    class loggingdict(dict): pass

    loggingdict()
    Call: dict.__new__(<class 'loggingdict'>)
    Call: dict.__init__({})

    ...

    @total_decorate(handler=my_custom_handler, name="logginglist")
    class _list(list): pass

    _list()
    Call: list.__new__(<class 'logginglist'>)
    Call: list.__init__([])

    ...

    loggingdict = total_decorate(dict, name="loggingdict")

    As demonstrated, this is possible to use this on user-created
    classes as well as built-in ones. This is very verbose and should
    only be used for debugging purposes.

    """

    if cls is None: # as an argument-only decorator
        return lambda cls: total_decorate(cls, handler=handler, name=name)

    namespace = {x: handler(getattr(cls, x)) for x in dir(cls) if x not in
                 ("__repr__", "__str__") and callable(getattr(cls, x))}

    bases = (cls,) + cls.__bases__

    if object in bases: # remove `object` from __bases__ (not __mro__)
        index = bases.index(object)
        bases = bases[:index] + bases[index+1:]

    return type(cls)(pick(name, cls.__name__), bases, namespace)

class attribute:
    """Class-level attribute for instance variables.

    >>> from logger.decorators import attribute
    >>> class Foo:
    ...     def __init__(self):
    ...         self.bar = 42
    ...     @attribute
    ...     def bar(self):
    ...         '''The answer to life, the universe, and everything.'''
    ...         print("This should not happen!")    
    ...         raise Exception("This will never be triggered")
    ...
    >>> Foo.bar
    The answer to life, the universe, and everything.
    >>> foo = Foo()
    >>> foo.bar
    42
    >>> class Bar:
    ...     @attribute
    ...     def baz(self):
    ...         raise Exception("Attribute 'baz' wasn't changed")
    ...
    >>> Bar.baz
    <attribute 'baz' of 'Bar' objects>
    >>> bar = Bar()
    >>> bar.baz
    <bound method Bar.baz of ...>
    >>> bar.baz()
    Traceback (most recent call last):
      ...
    Exception: Attribute 'baz' wasn't changed

    """

    def __init__(self, func):
        self.__func__ = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __get__(self, instance, owner):
        self.__objclass__ = owner
        if instance is None:
            return self
        return self.__func__.__get__(instance, owner)

    def __repr__(self):
        return (self.__doc__ or "<attribute %r of %r objects>" %
               (self.__name__, self.__objclass__.__name__))

class Singleton(type):
    """Create a unique name (similar to None).

    This creates a singleton from a class definition. The class will be
    instantiated, and it will be re-assigned with a special metaclass.
    If the class already used a metaclass, it will be used with the
    super metaclass. This mimics the behaviour of the built-in None.

    >>> from logger.decorators import Singleton
    >>> @Singleton
    ... class MySingleton: pass
    ...
    >>> MySingleton
    <Singleton 'MySingleton'>
    >>> MySingleton is type(MySingleton)()
    True
    >>> class Subclass(type(MySingleton)): pass
    ...
    Traceback (most recent call last):
      ...
    TypeError: type 'MySingleton' is not an acceptable base type

    """

    def __new__(cls, value, *args, _real=False):
        """Create a new singleton."""

        if (len(args) == 2 and
            isinstance(args[0], tuple) and
            isinstance(args[1], dict) and
            value == "singleton" and _real):
                return super().__new__(cls, value, *args)

        if args or _real:
            raise TypeError("Cannot use %r as a metaclass" % cls.__name__)

        meta = type(value) # get the proper metaclass

        class singleton(meta, metaclass=cls, _real=True):
            """Metaclass for magic singletons."""

            def __new__(*args, **kwargs):
                """Prevent subclassing."""
                try:
                    class M(type(None)): pass
                except TypeError as e:
                    raise TypeError(str(e).replace("NoneType",
                                    value.__name__)) from None

                raise TypeError("Cannot create metaclass")

        singleton.__qualname__ = singleton.__name__ = value.__name__
        singleton.__module__ = value.__module__

        names = dict(value.__dict__)

        if "__repr__" not in names:
            names["__repr__"] = lambda self: "<Singleton %r>" % value.__name__

        new = meta.__new__(singleton, value.__name__,
                           value.__bases__, names)

        ret = object.__new__(new)

        new.__new__ = lambda *args, **kwargs: ret

        return ret

    def __init__(*args, **kwargs):
        """Catch keyword arguments."""
