#!/usr/bin/env python3

"""Small utility functions for use in various places."""

__all__ = ["pick", "is_dunder", "find_name"]

import sys

def pick(arg, default):
    """Handler for default versus given argument."""
    return default if arg is None else arg

def is_dunder(name):
    """Return True if a __dunder__ name, False otherwise."""
    return name[:2] == name[-2:] == "__" and "_" not in (name[2:3], name[-3:-2])

def find_name(name, depth=0):
    """Find a name in the calling frame's scopes."""
    calling_frame = sys._getframe(depth + 2)
    if name in calling_frame.f_locals:
        return calling_frame.f_locals[name]
    if name in calling_frame.f_globals:
        return calling_frame.f_globals[name]
    if name in calling_frame.f_builtins:
        return calling_frame.f_builtins[name]

    raise NameError("could not find {!r}".format(name))
