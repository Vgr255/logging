#!/usr/bin/env python3

"""Various set implementations."""

__all__ = [ # Mutable versions; Immutable versions;      Ordered; Duplicates
            "Set",              "FrozenSet",             # [ ]       [ ]
            "MultiSet",         "FrozenMultiSet",        # [ ]       [X]
            "OrderedSet",       "FrozenOrderedSet",      # [X]       [ ]
            "OrderedMultiSet",  "FrozenOrderedMultiSet", # [X]       [X]
          ]

import collections
import itertools
import types

from .utilities import counter_to_iterable, count

class SetBase:
    """A base set implementation for all implementations."""

    _dict = dict

    def __iter__(self):
        """Yield all the items from the set."""
        for item, count in self._dict.items():
            yield from itertools.repeat(item, count)

    def __contains__(self, item):
        """Return True if the item is in the set, False otherwise."""
        return item in self._dict

    def __len__(self):
        """Return the number of items in the set."""
        return sum(self._dict.values())

    def __repr__(self):
        """Return the representation of the set."""
        return "{0}({1!r})".format(type(self).__name__, list(self))

    def __eq__(self, other):
        """Return True if both sets are equal."""
        if not isinstance(other, SetBase):
            return NotImplemented

        return self._dict == other._dict

    def __ne__(self, other):
        """Return True if both sets are not equal."""
        if not isinstance(other, SetBase):
            return NotImplemented

        return self._dict != other._dict

    def __lt__(self, other):
        """Return True if the set is a strict subset of the other set."""
        if not isinstance(other, SetBase):
            return NotImplemented

        if len(self) >= len(other):
            return False

        for item, value in self._dict.items():
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
        new = self._dict.fromkeys(x for x in self if x not in other)
        new.update((x, None) for x in other if x not in self)
        return type(self)(new)

    def __rxor__(self, other):
        """Return a set of the items only in one of the sets."""
        if not isinstance(other, SetBase):
            return NotImplemented
        new = other._dict.fromkeys(x for x in other if x not in self)
        new.update((x, None) for x in self if x not in other)
        return type(self)(new)

    def __or__(self, other):
        """Return a set of the items in either sets, or both."""
        if not isinstance(other, SetBase):
            return NotImplemented
        new = self._dict.fromkeys(self._dict)
        new.update(other._dict.fromkeys(other._dict))
        return type(self)(new)

    def __ror__(self, other):
        """Return a set of the items in either sets, or both."""
        if not isinstance(other, SetBase):
            return NotImplemented
        new = other._dict.fromkeys(other._dict)
        new.update(self._dict.fromkeys(self._dict))
        return type(self)(new)

    def __add__(self, other):
        """Return a set of all the items in the sets."""
        if not isinstance(other, SetBase):
            return NotImplemented
        new = self._dict.copy()
        new.update(other._dict)
        return type(self)(new)

    def __radd__(self, other):
        """Return a set of all the items in the sets."""
        if not isinstance(other, SetBase):
            return NotImplemented
        new = other._dict.copy()
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
        new = type(self._dict)()
        copy = self._dict.fromkeys(self._dict)
        for item in iterable:
            if item in copy and item not in new:
                new[item] = None
        return type(self)(new)

    def difference(self, iterable):
        """Return a set of the items in the set but not the iterable."""
        copy = self._dict.fromkeys(self._dict)
        for item in iterable:
            if item in copy:
                del copy[item]
        return type(self)(copy)

    def symmetric_difference(self, iterable):
        """Return a set of the items in one of the set or the iterable."""
        copy = self._dict.fromkeys(self._dict)
        to_add = type(self._dict)()
        to_remove = type(self._dict)()
        for item in iterable:
            if item not in copy:
                to_add[item] = None
            else:
                to_remove[item] = None

        new = self._dict.fromkeys(k for k in copy if k not in to_remove)
        new.update(to_add)
        return type(self)(new)

    def union(self, iterable):
        """Return a set of the items in both the set or iterable."""
        copy = self._dict.fromkeys(self._dict)
        for item in iterable:
            copy[item] = None
        return type(self)(copy)

    def sum(self, iterable):
        """Return a set of all the items in the set and iterable."""
        copy = self._dict.copy()
        for item in iterable:
            copy[item] = None
        return type(self)(copy)

    def count(self, item):
        """Return the number of times the item is in the set."""
        if item in self._dict:
            return self._dict[item]
        return 0

    def copy(self):
        """Return a shallow copy of self."""
        return type(self)(self._dict)

class MutableSetBase(SetBase):
    """A base set implementation for mutable sets."""

    def __init__(self, iterable=()):
        """Create a new mutable set."""
        self._dict = self._dict.fromkeys(iterable, 1)

    def __iand__(self, other):
        """Update the set with the items in both sets."""
        if not isinstance(other, SetBase):
            return NotImplemented

        for item in self._dict.copy():
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
                self._dict[item] = 1

        return self

    def __ior__(self, other):
        """Update the set with the items in both sets."""
        if not isinstance(other, SetBase):
            return NotImplemented

        for item in other:
            self._dict[item] = 1

        return self

    def __iadd__(self, other):
        """Update the set with all the items from the sets."""
        if not isinstance(other, SetBase):
            return NotImplemented

        for item in other:
            self._dict[item] = 1

        return self

    def add(self, item):
        """Add a new item to the set."""
        self._dict[item] = 1

    def discard(self, item):
        """Remove an item from the set if it exists."""
        self._dict.pop(item, None)

    def remove(self, item):
        """Remove an item from the set."""
        del self._dict[item]

    def drop(self, item):
        """Drop all instances of the item from the set."""
        del self._dict[item]

    def pop(self):
        """Remove and return a random item from the set."""
        if self._dict:
            return self._dict.popitem()[0]
        raise KeyError("pop from an empty set")

    def intersection_update(self, iterable):
        """Update the set with the items in both the set and iterable."""
        for item in self._dict.copy():
            if item not in iterable:
                del self._dict[item]

    def difference_update(self, iterable):
        """Update the set with the items not in the iterable."""
        for item in iterable:
            if item in self._dict:
                del self._dict[item]

    def symmetric_difference_update(self, iterable):
        """Update the set with the items in one of the set or iterable."""
        copy = self._dict.copy()
        for item in copy:
            if item in iterable:
                del self._dict[item]

        for item in iterable:
            if item not in copy:
                self._dict[item] = 1

    def union_update(self, iterable):
        """Update the set with the items in both the set or iterable."""
        for item in iterable:
            self._dict[item] = 1

    def sum_update(self, iterable):
        """Update the set with all the items from the set and iterable."""
        for item in iterable:
            self._dict[item] = 1

    def update(self, iterable):
        """Update the set with the iterable."""
        for item in iterable:
            self._dict[item] = 1

    def clear(self):
        """Clear the set."""
        self._dict.clear()

class ImmutableSetBase(SetBase):
    """A base set implementation for immutable sets."""

    def __new__(cls, iterable=()):
        """Create a new immutable set."""
        new = self._dict.fromkeys(iterable, 1)
        self = super().__new__(cls)
        self._dict = types.MappingProxyType(new)
        return self

    def __hash__(self):
        """Return the hash of the set."""
        return hash(tuple(self._dict.items()))

class OrderedSetBase(SetBase):
    """A base ordered set implementation for the ordered versions.

    Indexing an ordered set is supported, but is not very efficient.
    See the information below on indexing and deleting items. Getting
    or deleting an item with its index is O(n), while using a slice or
    tuple as indices is O(log n).

    Furthermore, the items in an ordered set are ordered by the first
    item's insert location, should there be duplicates. If an arbitrary
    order (including re-ordering) is desired, a list is recommended.

    Indexing a set using an int (or int-like) object returns the item
    at that position. Indexing using a slice recursively iterates over
    the set with each integer in the slice, and returns a new set.
    Finally, indexing with a tuple recursively iterates over the set
    and returns a tuple of the elements.

    Assigning to an index makes no sense for a set (even ordered), and
    is not supported. However, deleting from an index is somewhat less
    senseless. Doing `del oset[i]` is approximately equivalent (mostly
    in regards to performance) to `oset.remove(oset[i])`. Valid indices
    include ints (or int-like), slices, and tuples. Please note that,
    since tuples can contain an arbitrary number of nested structures,
    passing in tuples to delete items has an exponential runtime cost.

    """

    _dict = collections.OrderedDict

    def __getitem__(self, index):
        """Get the item at index given."""
        if hasattr(index, "__index__"):
            if index >= 0:
                it = iter(self._dict)
            else:
                it = reversed(self._dict)
                index = -index

            for i in range(index):
                try:
                    next(it)
                except StopIteration:
                    raise IndexError("set index out of range")

            try:
                return next(it)
            except StopIteration:
                raise IndexError("set index out of range")

        elif isinstance(index, slice):
            new = type(self._dict)()
            for i in range(*index.indices(len(self))):
                try:
                    item = self[i]
                except IndexError:
                    continue

                if item not in new:
                    new[item] = 0
                new[item] += 1

            return type(self)(counter_to_iterable(new))

        elif isinstance(index, tuple):
            new = []
            for item in index:
                new.append(self[item])
            return tuple(new)

        else:
            raise TypeError("set indices must be integers, slices or tuples, "
                            "not {0}".format(type(index).__name__))

    def __delitem__(self, index):
        """Remove the item at position given."""
        if hasattr(index, "__index__"):
            self.remove(self[index])

        elif isinstance(index, slice):
            for i in range(*index.indices(len(self))):
                try:
                    self.remove(self[i])
                except (IndexError, KeyError):
                    continue

        elif isinstance(index, tuple):
            for item in index:
                del self[item]

        else:
            raise TypeError("set indices must be integers, slices or tuples, "
                            "not {0}".format(type(index).__name__))

    def __reversed__(self):
        """Yield all the items from the set in reverse order."""
        yield from reversed(self._dict)

    def find(self, item):
        """Return the index of the item in the set, or -1 if it's not in."""
        item_hash = hash(item) # If it's not hashable, it cannot be in a set
        for i, value in enumerate(self._dict):
            if hash(value) == item_hash and value == item:
                return i

        return -1

    def index(self, item):
        """Return the index of the item in the set if it exists."""
        value = self.find(item)
        if value == -1
            raise ValueError("{!r} is not in set".format(item))
        return value

class MultiSetBase(SetBase):
    """A base multiset implementation for both multiset versions."""

    def issubset(self, iterable):
        """Return True if the set is a subset of the iterable."""
        counter = count(iterable)

        for item, value in self._dict.items():
            if item not in counter or counter[item] < value:
                return False

        return True

    def issuperset(self, iterable):
        """Return True if the set is a superset of the iterable."""
        for item, value in count(iterable).items():
            if item not in self._dict or self._dict[item] < value:
                return False

        return True

    def intersection(self, iterable):
        """Return a set of the items from both the set and iterable."""
        new = type(self._dict)()
        copy = self._dict.copy()
        for item in iterable:
            if item in copy and copy[item] > 0:
                if item not in new:
                    new[item] = 0
                new[item] += 1
                copy[item] -= 1
        return type(self)(counter_to_iterable(new))

    def difference(self, iterable):
        """Return a set of the items in the set but not the iterable."""
        copy = self._dict.copy()
        for item in iterable:
            if item in copy and copy[item] > 0:
                copy[item] -= 1
        return type(self)(counter_to_iterable(copy))

    def symmetric_difference(self, iterable):
        """Return a set of the items in either the set or the iterable."""
        new = type(self._dict)()
        copy = self._dict.copy()
        counter = count(iterable)

        for item in itertools.chain(copy, counter):
            new[item] = abs(copy.get(item, 0) - counter.get(item, 0))

        return type(self)(counter_to_iterable(new))

    def union(self, iterable):
        """Return a set with one of each of the items."""
        new = self._dict.fromkeys(self._dict)
        for item in iterable:
            new[item] = None
        return type(self)(new)

    def sum(self, iterable):
        """Return a set of all items and their counts."""
        new = self._dict.copy()
        for item in iterable:
            if item not in new:
                new[item] = 0
            new[item] += 1
        return type(self)(counter_to_iterable(new))

class Set(MutableSetBase):
    """A mutable and unordered set which does not allow duplicates."""

class FrozenSet(ImmutableSetBase):
    """An immutable and unordered set which does not allow duplicates."""

class MultiSet(MutableSetBase, MultiSetBase):
    """A mutable and unordered set which allows duplicates."""

    def __init__(self, iterable=()):
        """Create a new mutable multiset."""
        self._dict = count(iterable)

    def __iand__(self, other):
        """Update the set with the items in both sets."""
        if not isinstance(other, SetBase):
            return NotImplemented

        copy = self._dict.copy()

        for item, value in copy.items():
            count = min(other.count(item), value)
            if count:
                self._dict[item] = count
            else:
                del self._dict[item]

        return self

    def __isub__(self, other):
        """Update the set with the items not in the other set."""
        if not isinstance(other, SetBase):
            return NotImplemented

        copy = self._dict.copy()

        for item, value in copy.items():
            count = value - other.count(item)
            if count > 0:
                self._dict[item] = count
            else:
                del self._dict[item]

        return self

    def __ixor__(self, other):
        """Update the set with the items in only one set."""
        if not isinstance(other, SetBase):
            return NotImplemented

        copy = self._dict.copy()

        for item, value in copy.items():
            count = abs(value - other.count(item))
            if count:
                self._dict[item] = count
            else:
                del self._dict[item]

        for item, value in other._dict.items():
            if item in copy:
                continue # already did it

            self._dict[item] = value

        return self

    def __ior__(self, other):
        """Update the set with the items in both sets."""
        if not isinstance(other, SetBase):
            return NotImplemented

        for item in itertools.chain(self._dict, other._dict):
            self._dict[item] = 1 # we don't care about the count

        return self

    def __iadd__(self, other):
        """Update the set with all the items in both sets."""
        if not isinstance(other, SetBase):
            return NotImplemented

        for item, value in other._dict.items():
            self._dict[item] = self._dict.get(item, 0) + value

        return self

    def add(self, item):
        """Add a new item to the set."""
        if item not in self._dict:
            self._dict[item] = 1
        else:
            self._dict[item] += 1

    def discard(self, item):
        """Remove an item from the set if it exists."""
        if item in self._dict:
            self._dict[item] -= 1
            if self._dict[item] <= 0:
                del self._dict[item]

    def remove(self, item):
        """Remove an item from the set."""
        self._dict[item] -= 1 # Raises a KeyError if not present
        if self._dict[item] <= 0:
            del self._dict[item]

    def pop(self):
        """Remove and return a random item from the set."""
        if not self._dict:
            raise KeyError("pop from empty set")

        item = next(iter(self._dict))
        if self._dict[item] == 1:
            del self._dict[item]
            return item

        self._dict[item] -= 1
        return item

    def intersection_update(self, iterable):
        """Update the set with the items in both the set and iterable."""
        copy = self._dict.copy()
        counter = count(iterable)

        for item, value in copy.items():
            count = min(value, counter.get(item, 0))
            if not count:
                del self._dict[item]
            else:
                self._dict[item] = count

    def difference_update(self, iterable):
        """Update the set with the items not in the iterable."""
        for item, value in count(iterable).items():
            if item in self._dict:
                self._dict[item] -= value
                if self._dict[item] <= 0:
                    del self._dict[item]

    def symmetric_difference_update(self, iterable):
        """Update the set with the items in one of the set or iterable."""
        copy = self._dict.copy()
        counter = count(iterable)

        for item, value in copy.items():
            count = abs(value - counter.get(item, 0))
            if count:
                self._dict[item] = count
            else:
                del self._dict[item]

        for item, value in counter.items():
            if item in copy:
                continue # already done it above
            self._dict[item] = value

    def union_update(self, iterable):
        """Update the set with the items from both the set and iterable."""
        for item in itertools.chain(self._dict, iterable):
            self._dict[item] = 1

    def sum_update(self, iterable):
        """Update the set with all items from the set and iterable."""
        for item in iterable:
            if item not in self._dict:
                self._dict[item] = 0
            self._dict[item] += 1

    def update(self, iterable):
        """Update the set with all items from the iterable."""
        for item in iterable:
            if item not in self._dict:
                self._dict[item] = 0
            self._dict[item] += 1

class FrozenMultiSet(ImmutableSetBase, MultiSetBase):
    """An immutable and unordered set which allows duplicates."""

    def __new__(cls, iterable=()):
        new = count(iterable)
        self = super().__new__(cls)
        self._dict = types.MappingProxyType(new)
        return self

class OrderedSet(OrderedSetBase, Set):
    """A mutable and ordered set which does not allow duplicates."""

class FrozenOrderedSet(OrderedSetBase, FrozenSet):
    """An immutable and ordered set which does not allow duplicates."""

class OrderedMultiSet(OrderedSetBase, MultiSet):
    """A mutable and ordered set which allows duplicates."""

class FrozenOrderedMultiSet(OrderedSetBase, FrozenMultiSet):
    """An immutable and ordered set which allows duplicates."""
