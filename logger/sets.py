#!/usr/bin/env python3

"""Various set implementations."""

__all__ = []

import types

from .utilities import counter_to_iterable

class SetBase:
    """A base set implementation for all implementations."""

    def __iter__(self):
        """Yield all the items from the set."""
        yield from self._dict

    def __contains__(self, item):
        """Return True if the item is in the set, False otherwise."""
        return item in self._dict

    def __len__(self):
        """Return the number of items in the set."""
        return len(self._dict)

    def __repr__(self):
        """Return the representation of the set."""
        return "{0}([{1}])".format(type(self).__name__,
                                   ", ".join(repr(x) for x in self))

    def __reduce__(self):
        """Return the set state for pickling."""
        return type(self), (list(self),), None

    def __reduce_ex__(self, proto=3):
        """Return the advanced set state for pickling."""
        return type(self), (list(self),), None

    def __copy__(self):
        """Return a shallow copy of the set."""
        return type(self)(self._dict)

    def __deepcopy__(self, memo):
        """Return a deep copy of the set."""
        return type(self)(self._dict)

    def __eq__(self, other):
        """Return True if both sets are equal."""
        if not isinstance(other, SetBase):
            return NotImplemented

        if len(self) != len(other):
            return False

        for item, value in self._dict.items():
            if item not in other._dict or other._dict[item] != value:
                return False

        return True

    def __ne__(self, other):
        """Return True if both sets are not equal."""
        if not isinstance(other, SetBase):
            return NotImplemented

        if len(self) != len(other):
            return True

        for item, value in self._dict.items():
            if item not in other._dict or other._dict[item] != value:
                return True

        return False

    def __lt__(self, other):
        """Return True if the set is a strict subset of the other set."""
        if not isinstance(other, SetBase):
            return NotImplemented

        if len(self) >= len(other):
            return False

        for item, value in self._dict.items():
            if value is None:
                value = 1
            if item not in other._dict or other._dict[item] < value:
                return False

        return True

    def __le__(self, other):
        """Return True if the set is a subset of the other set."""
        if not isinstance(other, SetBase):
            return NotImplemented

        if len(self) > len(other):
            return False

        for item, value in self._dict.items():
            if value is None:
                value = 1
            if item not in other._dict or other._dict[item] < value:
                return False

        return True

    def __gt__(self, other):
        """Return True if the set is a strict superset of the other set."""
        if not isinstance(other, SetBase):
            return NotImplemented

        if len(self) <= len(other):
            return False

        for item, value in other._dict.items():
            if value is None:
                value = 1
            if item not in self._dict or self._dict[item] < value:
                return False

        return True

    def __ge__(self, other):
        """Return True if the set is a superset of the other set."""
        if not isinstance(other, SetBase):
            return NotImplemented

        if len(self) < len(other):
            return False

        for item, value in other._dict.items():
            if value is None:
                value = 1
            if item not in self._dict or self._dict[item] < value:
                return False

        return True

    def __and__(self, other):
        """Return a set of the common items."""
        if not isinstance(other, SetBase):
            return NotImplemented
        return type(self)(x for x in self if x in other)

    def __rand__(self, other):
        """Return a set of the common items."""
        if not isinstance(other, SetBase):
            return NotImplemented
        return type(self)(x for x in other if x in self)

    def __sub__(self, other):
        """Return a set of the items not in the other set."""
        if not isinstance(other, SetBase):
            return NotImplemented
        return type(self)(x for x in self if x not in other)

    def __rsub__(self, other):
        """Return a set of the items not in the set."""
        if not isinstance(other, SetBase):
            return NotImplemented
        return type(self)(x for x in other if x not in self)

    def __xor__(self, other):
        """Return a set of the items only in one of the sets."""
        if not isinstance(other, SetBase):
            return NotImplemented
        new = {x: None for x in self if x not in other}
        new.update({x: None for x in other if x not in self})
        return type(self)(new)

    def __rxor__(self, other):
        """Return a set of the items only in one of the sets."""
        if not isinstance(other, SetBase):
            return NotImplemented
        new = {x: None for x in other if x not in self}
        new.update({x: None for x in self if x not in other})
        return type(self)(new)

    def __or__(self, other):
        """Return a set of the items in either sets, or both."""
        if not isinstance(other, SetBase):
            return NotImplemented
        new = dict.fromkeys(self._dict)
        new.update(dict.fromkeys(other._dict))
        return type(self)(new)

    def __ror__(self, other):
        """Return a set of the items in either sets, or both."""
        if not isinstance(other, SetBase):
            return NotImplemented
        new = dict.fromkeys(other._dict)
        new.update(dict.fromkeys(self._dict))
        return type(self)(new)

    def __add__(self, other):
        """Return a set of all the items in the sets."""
        if not isinstance(other, SetBase):
            return NotImplemented
        new = dict(self._dict)
        new.update(other._dict)
        return type(self)(new)

    def __radd__(self, other):
        """Return a set of all the items in the sets."""
        if not isinstance(other, SetBase):
            return NotImplemented
        new = dict(other._dict)
        new.update(self._dict)
        return type(self)(new)

    def issubset(self, iterable):
        """Return True if the set if a subset of the iterable."""
        for item in self:
            if item not in iterable:
                return False
        return True

    def issuperset(self, iterable):
        """Return True if the set if a superset of the iterable."""
        for item in iterable:
            if item not in self:
                return False
        return True

    def isdisjoint(self, iterable):
        """Return True if the set and iterable have no items in common."""
        for item in self:
            if item in iterable:
                return False

        for item in iterable:
            if item in self:
                return False

        return True

    def intersection(self, iterable):
        """Return a set of the items from both the set and iterable."""
        new = {}
        copy = dict.fromkeys(self._dict)
        for item in iterable:
            if item in copy and item not in new:
                new[item] = None
        return type(self)(new)

    def difference(self, iterable):
        """Return a set of the items in the set but not the iterable."""
        copy = dict.fromkeys(self._dict)
        for item in iterable:
            if item in copy:
                del copy[item]
        return type(self)(copy)

    def symmetric_difference(self, iterable):
        """Return a set of the items in one of the set or the iterable."""
        copy = dict.fromkeys(self._dict)
        to_add = {}
        to_remove = {}
        for item in iterable:
            if item not in copy:
                to_add[item] = None
            else:
                to_remove[item] = None

        new = {k: None for k in copy if k not in to_remove}
        new.update(to_add)
        return type(self)(new)

    def union(self, iterable):
        """Return a set of the items in both the set or iterable."""
        copy = dict.fromkeys(self._dict)
        for item in iterable:
            copy[item] = None
        return type(self)(copy)

    def sum(self, iterable):
        """Return a set of all the items in the set and iterable."""
        copy = dict(self._dict)
        for item in iterable:
            copy[item] = None
        return type(self)(copy)

    def copy(self, *, deep=False):
        """Return a deep or shallow copy of self."""
        if deep:
            return type(self).__deepcopy__(self, {})
        return type(self).__copy__(self)

class MutableSetBase(SetBase):
    """A base set implementation for mutable sets."""

    def __init__(self, iterable=()):
        """Create a new mutable set."""
        self._dict = {x: None for x in iterable}

    def __iand__(self, other):
        """Update the set with the items in both sets."""
        if not isinstance(other, SetBase):
            return NotImplemented

        for item in dict(self._dict):
            if item not in other._dict:
                del self._dict[item]

        return self

    def __isub__(self, other):
        """Update the set without the items in the other set."""
        if not isinstance(other, SetBase):
            return NotImplemented

        for item in other._dict:
            if item in self._dict:
                del self._dict[item]

        return self

    def __ixor__(self, other):
        """Update the set with the items in only one set."""
        if not isinstance(other, SetBase):
            return NotImplemented

        for item in other._dict:
            if item in self._dict:
                del self._dict[item]
            else:
                self._dict[item] = None

        return self

    def __ior__(self, other):
        """Update the set with the items in both sets."""
        if not isinstance(other, SetBase):
            return NotImplemented

        for item in other:
            self._dict[item] = None

        return self

    def __iadd__(self, other):
        """Update the set with all the items from the sets."""
        if not isinstance(other, SetBase):
            return NotImplemented

        for item in other:
            self._dict[item] = None

        return self

    def add(self, item):
        """Add a new item to the set."""
        self._dict[item] = None

    def discard(self, item):
        """Remove an item from the set if it exists."""
        self._dict.pop(item, None)

    def remove(self, item):
        """Remove an item from the set."""
        del self._dict[item]

    def pop(self):
        """Remove and return a random item from the set."""
        if self._dict:
            return self._dict.popitem()[0]
        raise KeyError("pop from an empty set")

    def intersection_update(self, iterable):
        """Update the set with the items in both the set and iterable."""
        for item in dict(self._dict):
            if item not in iterable:
                del self._dict[item]

    def difference_update(self, iterable):
        """Update the set with the items not in the iterable."""
        for item in iterable:
            if item in self._dict:
                del self._dict[item]

    def symmetric_difference_update(self, iterable):
        """Update the set with the items in one of the set or iterable."""
        for item in dict(self._dict):
            if item in iterable:
                del self._dict[item]

    def union_update(self, iterable):
        """Update the set with the items in both the set or iterable."""
        for item in iterable:
            self._dict[item] = None

    def sum_update(self, iterable):
        """Update the set with all the items from the set and iterable."""
        for item in iterable:
            self._dict[item] = None

    def update(self, iterable):
        """Update the set with the iterable."""
        self.sum_update(iterable)

    def clear(self):
        """Clear the set."""
        self._dict.clear()

class ImmutableSetBase(SetBase):
    """A base set implementation for immutable sets."""

    def __new__(cls, iterable=()):
        """Create a new immutable set."""
        new = {x: None for x in iterable}
        self = super().__new__(cls)
        self._dict = types.MappingProxyType(new)
        return self

    def __hash__(self):
        """Return the hash of the set."""
        return hash(tuple(self._dict.items()))

class OrderedSetBase(SetBase):
    """A base ordered set implementation for the ordered versions."""

    def __reversed__(self):
        """Yield all the items from the set in reverse order."""
        yield from reversed(self._dict)
