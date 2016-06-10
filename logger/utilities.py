#!/usr/bin/env python3

"""Small utility functions for use in various places."""

__all__ = ["pick", "is_dunder", "find_name"]

import collections

def pick(arg, default):
    """Handler for default versus given argument."""
    return default if arg is None else arg

def is_dunder(name):
    """Return True if a __dunder__ name, False otherwise."""
    return name[:2] == name[-2:] == "__" and "_" not in (name[2:3], name[-3:-2])

def convert_to_od(mapping, order):
    """Convert mapping to an OrderedDict instance using order."""
    return collections.OrderedDict([(i, mapping[i]) for i in order])

def sorter(x):
    """Make sure non-string objects are last."""
    # this is very ugly and I am not pleased with it, so if anyone can
    # come up with a better solution, I'm all open
    # see http://bugs.python.org/issue20630 and
    #     http://bugs.python.org/issue20632
    if "__lt__" not in type(x).__dict__:
        return "????????"
    if not isinstance(x, str):
        return "????" + str(x).lower()
    return x.lower()
