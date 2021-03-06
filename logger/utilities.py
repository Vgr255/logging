#!/usr/bin/env python3

"""Small utility functions for use in various places."""

__all__ = ["pick", "is_dunder", "convert_to_od",
           "counter_to_iterable", "count"]

import collections
import itertools

def pick(arg, default):
    """Handler for default versus given argument."""
    return default if arg is None else arg

def is_dunder(name):
    """Return True if a __dunder__ name, False otherwise."""
    return name[:2] == name[-2:] == "__" and "_" not in (name[2:3], name[-3:-2])

def convert_to_od(mapping, order):
    """Convert mapping to an OrderedDict instance using order."""
    return collections.OrderedDict([(i, mapping[i]) for i in order])

def counter_to_iterable(mapping):
    """Convert a counter (mapping) to an iterable / iterator."""
    for item in itertools.starmap(itertools.repeat, mapping.items()):
        yield from item

def count(iterable, mapping):
    """Return an instance of 'mapping' with {item: count} items."""
    items = mapping()

    for item in iterable:
        if item not in items:
            items[item] = 0
        items[item] += 1

    return items
