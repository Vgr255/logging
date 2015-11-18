#!/usr/bin/env python3

import collections
import inspect
import sys
import gc

arguments = collections.namedtuple("arguments",
            "name value checker annotation")

def get_function(depth=0):
    """Return the function you are currently in."""

    funcs = []

    frame = sys._getframe(depth + 1)
    code = frame.f_code
    fglobals = frame.f_globals

    for func in gc.get_referrers(code):
        if inspect.isfunction(func) or inspect.ismethod(func):
            if func.__code__ is code and func.__globals__ is fglobals:
                funcs.append(func)

    if len(funcs) == 1:
        return funcs[0]

def chk_def(*olds, handler=None, parser=None, msg=[], func=[],
                   HAS_VALUE=0b01, HAS_ANNOTATION=0b10):
    """Parse the function and method definitions. This is recursive.

    This can be used to parse functions, methods, classes and
    modules, recursively (except for modules). It can accept any
    number of arguments, of any of the aforementioned types.

    """

    if handler is parser is None:
        from . import BaseLogger
        handler = BaseLogger().logger

    for runner in olds:

        name = inspect.getmodule(runner)

        if name in (sys.modules["builtins"], None):
            continue
        elif inspect.isclass(parser):
            mod = sys.modules[parser.__module__]
        elif inspect.ismodule(parser):
            mod = sys.modules[parser.__name__]
        elif name.__name__ in sys.modules:
            mod = name
        elif hasattr(runner, "__name__"):
            mod = runner
        else:
            continue

        if msg:
            pass
        elif hasattr(mod, "__file__"):
            msg.append("Reading file %r\n" % mod.__file__)
        elif hasattr(mod, "__module__"):
            msg.append("Reading class %r" % mod.__name__)
        else:
            msg.append("Reading module %r" % mod.__name__)

        name = name.__name__

        if inspect.ismethod(runner):
            fn = runner.__func__
            func.append((fn.__qualname__, "Method %r of class " + c, fn))
            msg.append("Parsing method %r" % fname)

        elif inspect.isclass(runner):
            msg.append("Parsing class " + runner.__name__)
            chk_def(*runner.__dict__.values(), parser=runner)

        # prevent recursive calls for modules, as that would lead
        # to an infinite (or arbitrarily long and memory-eating)
        # loop that could iterate over half of the standard library
        # modules... so, yeah, don't let that happen
        elif inspect.ismodule(runner) and not parser:
            msg.append("Parsing module %r" % runner.__name__)
            chk_def(*runner.__dict__.values(), parser=runner)

        elif inspect.isfunction(runner) or inspect.isgenerator(runner):
            name = runner.__qualname__
            code = getattr(runner, "__code__",
                   getattr(runner, "gi_code", None))

            gen = "generator " if code.co_flags & inspect.CO_GENERATOR else ""

            if inspect.isclass(parser):
                func.append((name, (gen + "method %r of class ").capitalize()
                             + parser.__name__, runner))
                msg.append("Parsing %smethod %r" % (gen, name))
            else:
                func.append((name, (gen + "function %r").capitalize(),
                             runner))
                msg.append("Parsing %sfunction %r" % (gen, name))

    if handler is None and parser is not None:
        return

    for path, name, function in func:

        if inspect.isfunction(function) or inspect.ismethod(function):

            code = function.__code__

            lineno = code.co_firstlineno
            fname = code.co_name

            msg.append("\n%s at line %r" % ((name % fname), lineno))

            func_def = parse_def(function, HAS_VALUE, HAS_ANNOTATION)
            args = []
            ret = None

            for fn in func_def:
                if fn.name == "return":
                    ret = fn
                    continue
                string = fn.name
                if fn.checker & HAS_ANNOTATION:
                    string += ": %r" % (fn.annotation,)
                if fn.checker & HAS_VALUE:
                    string += "=%r" % (fn.value,)
                args.append(string)

            string = "Definition: %s(%s)" % (path, ", ".join(args))

            if ret is not None:
                string += " -> %r" % ret.annotation

            msg.append(string)

    if handler is not None and parser is None:
        handler("\n".join(msg))

        msg.clear()
        func.clear()

def parse_def(function, HAS_VALUE=0b01, HAS_ANNOTATION=0b10):
    """Parse a function definition. Return a list of arguments."""

    params = []

    if inspect.isfunction(function) or inspect.ismethod(function):

        code = function.__code__

        fname = code.co_name
        lineno = code.co_firstlineno
        flags = code.co_flags

        defargs = function.__defaults__ or ()
        kwdefargs = function.__kwdefaults__ or {}
        annotations = function.__annotations__

        num = code.co_argcount + code.co_kwonlyargcount

        total = num + (bool(flags & inspect.CO_VARARGS) +
                       bool(flags & inspect.CO_VARKEYWORDS))

        args_all = kwargs_all = None

        if flags & inspect.CO_VARKEYWORDS:
            kwargs_all = code.co_varnames[num+bool(flags & inspect.CO_VARARGS)]

        if flags & inspect.CO_VARARGS:
            args_all = code.co_varnames[num]

        elif code.co_kwonlyargcount:
            args_all = ""

        varnames = code.co_varnames[:total]

        defaults = len(defargs) + len(kwdefargs) + (total - num)

        if code.co_argcount:
            if defaults > 0:
                lister = varnames[:-defaults]
            else:
                lister = varnames
            for arg in lister:
                ret = 0
                if arg in annotations:
                    ret += HAS_ANNOTATION
                params.append(arguments(arg, None, ret,
                              annotations.get(arg)))

        if defargs:
            named_pos = code.co_argcount - len(defargs)
            union_vars = varnames[named_pos:code.co_argcount]
            union = [[v] for v in union_vars]
            union = [union[i] + [v] for i, v in enumerate(defargs)]
            for arg, val in union:
                ret = HAS_VALUE
                if arg in annotations:
                    ret += HAS_ANNOTATION
                params.append(arguments(arg, val, ret, annotations.get(arg)))

        if args_all is not None:
            ret = 0
            if args_all in annotations:
                ret += HAS_ANNOTATION
            params.append(arguments("*" + args_all, None, ret,
                          annotations.get(args_all)))

        if kwdefargs:
            for arg, val in kwdefargs.items():
                ret = HAS_VALUE
                if arg in annotations:
                    ret += HAS_ANNOTATION
                params.append(arguments(arg, val, ret, annotations.get(arg)))

        if kwargs_all:
            ret = 0
            if kwargs_all in annotations:
                ret += HAS_ANNOTATION
            params.append(arguments("**" + kwargs_all, None, ret,
                          annotations.get(kwargs_all)))

        if "return" in annotations:
            params.append(arguments("return", None, HAS_ANNOTATION,
                          annotations["return"]))

    return params
