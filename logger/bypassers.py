#!/usr/bin/env python3

"""Implementation of the Bypassers handlers."""

from datetime import datetime
import time
import sys

__all__ = ["NoValue", "BaseBypassers", "TypeBypassers", "LevelBypassers"]

def is_dunder(name):
    """Return True if a __dunder__ name, False otherwise."""
    return name[:2] == name[-2:] == "__" and "_" not in (name[2], name[-3])

def is_hashable(obj): # taken from collections.Hashable
    """Return True if obj is hashable, False otherwise."""
    for cls in obj.__class__.__mro__:
        if "__hash__" in cls.__dict__:
            if cls.__dict__["__hash__"]:
                return True
            return False

def sorter(x):
    # this is very ugly and I am not pleased with it, so if anyone can
    # come up with a better solution, I'm all open
    # see http://bugs.python.org/issue20630 and
    #     http://bugs.python.org/issue20632
    """Make sure non-string objects are last."""
    if "__lt__" not in type(x).__dict__:
        return "????????"
    if not isinstance(x, str):
        return "????" + str(x)
    return x.lower()

class MetaNoValue(type):
    """Metaclass responsible for ensuring uniqueness."""

    def __new__(meta, cls, bases, clsdict):
        """Ensure there is one (and only one) NoValue singleton."""
        if "_novalue" not in sys.modules:
            nv = super().__new__(meta, cls, bases, clsdict)()
            nv.__class__.__new__ = lambda cls: nv
            sys.modules["_novalue"] = nv
            return nv
        raise TypeError("type 'NoValue' is not an acceptable base type")

class NoValue(sys.__class__, metaclass=MetaNoValue):
    """Express the lack of value, as None has a special meaning."""

    def __init__(self):
        """Instantiate the module with the class' name."""
        cls = self.__class__
        super(cls, self).__init__(cls.__name__, cls.__doc__)

    def __repr__(self):
        """Return the explicit NoValue string."""
        return 'NoValue'

    def __bool__(self):
        """Return False no matter what."""
        return False

class BypassersIterator:
    """Special iterator for the members of a Bypassers instance.

    This iterator takes a Bypassers instance as the first parameter. It
    can accept a second, optional parameter, which is used to determine
    how to iterate through the mapping. Leaving this undefined or using
    any other value than the ones stated here will iterate through the
    keys in alphabetical order. If constructed from an external source
    (such as iter), the method can be changed through iterator.method,
    before calling iter() on itself. Changing the method used can be done
    before the iterator is created.

    The valid names for the iteration method are as follow:

    'name':
                Return all items in order from the first view object,
                then from the second, and up to the last. The items are
                iterated one at a time.

    'all':
                Return all items in order from the first view object,
                then from the second, and up to the last. The items are
                iterated all in one batch.

    'index':
                Return the first item from all view objects, then from
                the second view object, and so on to the last one. The
                items are iterated one at a time.

    'grouped':
                Return the first item from all view objects, then from
                the second view object, and so on to the last one. The
                items are iterated all in one batch.

    """

    def __init__(self, instance, reverse=False, method=None):
        """Create a new bypassers iterator."""
        self.iterator = None
        self.instance = instance
        self.reverse = reverse
        self.method = method

    def __setattr__(self, name, value):
        """Disallow attribute changing when the iterator exists."""
        if hasattr(self, name) and self.iterator is not None:
            raise RuntimeError(("cannot change attribute %r after the " +
                                "iterator has been constructed") % name)
        super().__setattr__(name, value)

    def __iter__(self):
        """Return the iterator object."""
        self.iterator = bypassers_iterator(self.instance, self.reverse,
                                                          self.method)
        return self

    def __next__(self):
        """Return the next item in the list."""
        if self.iterator is None:
            raise RuntimeError("no iterator was constructed")
        return next(self.iterator)

def bypassers_iterator(instance, reverse, method):
    """Inner iterator for the bypassers iterator."""

    step = (reverse * 2 - 1) * -1

    if method == "name":
        for name in instance.__names__:
            for i in range(0, len(instance), step):
                yield getattr(instance, name)[i]

    elif method == "index":
        for i in range(0, len(instance), step):
            for name in instance.__names__:
                yield getattr(instance, name)[i]

    elif method == "grouped":
        for i in range(0, len(instance), step):
            names = []
            for name in instance.__names__:
                names.append(getattr(instance, name)[i])
            yield names

    elif method == "all":
        for name in instance.__names__:
            yield getattr(instance, name)

    else:
        iterator = iter(sorted(instance.keys(), key=sorter, reverse=reverse))
        while True:
            yield next(iterator)

class Container:
    """Base container class for various purposes."""

    def __init__(self, items):
        """Create a new items set."""
        if items in (None, NoValue):
            items = set()
        if isinstance(items, type):
            items = items() # pass in 'list' to create a new list, etc
        self._items = items

    def __iter__(self):
        """Return an iterator over the items of self."""
        return iter(sorted(self._items, key=sorter))

    def __len__(self):
        """Return the amount of items in self."""
        return len(self._items)

    def __contains__(self, item):
        """Return True if item is in self."""
        return item in self._items

    def __str__(self):
        """Return a string of all items."""
        return "%s(%s)" % (self.__class__.__name__,
               ", ".join(repr(item) for item in self))

    def __repr__(self):
        """Return a representation of the items in self."""
        return repr(self._items)

    def __dir__(self):
        """Return a list of all methods."""
        return set(dir(self.__class__) + list(x for x in self.__dict__
                                   if x[0] != "_" or is_dunder(x)))

    def __eq__(self, other):
        """Return self == other."""
        try:
            if self._items == other._items:
                return True
            if frozenset(self._items) == frozenset(other):
                return True
        except Exception:
            return False
        return False

    def __ne__(self, other):
        """Return self != other."""
        return not (self == other)

class BaseMapping(Container):
    """Lightweight class for inner iteration."""

    def __add__(self, items):
        """Return a new iterable with all items."""
        new = self._items.copy()
        new.update(items)
        return self.__class__(new)

    __radd__ = __add__ # same thing

    def __iadd__(self, items):
        """Update and return self with items."""
        self._items.update(items)
        return self._items

    def __getattr__(self, attr):
        """Delegate an attribute not found to the items set."""
        return getattr(self._items, attr)

class Viewer(Container):
    """Viewer object for the Bypassers mapping."""

    def __init__(self, self_):
        """Create a new viewer handler."""
        self.self = self_
        self._items = self_._items

    def __str__(self):
        """Return a string of self."""
        return "%s(%s)" % (self.self.__class__.__name__,
               ", ".join(repr(item) for item in self))

    def __getitem__(self, index_):
        """Return the matching value."""
        return self._items[index_]

class BaseViewer:
    """Base viewer class for the Bypassers mapping."""

    def __init__(self):
        """Create a new view object."""
        self._items = []
        self._viewer = Viewer(self)

    def __getitem__(self, index_):
        """Return the item at the index given."""
        return self._items[index_]

    def __setitem__(self, index_, item):
        """Assign the item at the index given."""
        self._items[index_] = item

    def __delitem__(self, index_):
        """Remove the item at the index given."""
        del self._items[index_]

    def __dir__(self):
        """Return a list of all methods."""
        return dir(self.__class__)

    def __repr__(self):
        """Return a representation of the viewer."""
        n = len(__name__) + 2
        return "<" + super().__repr__()[n:].replace(" object", " view object")

    def __call__(self):
        """Return the view object."""
        return self._viewer

    def __getattr__(self, attr):
        """Delegate any attribute not found to the inner list."""
        return getattr(self._items, attr)

def make_sub(name, names):
    """Generate view objects."""
    subs = []
    for sub in names:
        sub = sub.capitalize()
        doc = """Return all the %s of the %s class.""" % (sub.lower(), name)
        subs.append(type(name + sub, (BaseViewer,), {"__doc__": doc}))
    return subs

class BypassersMeta(type):
    """Metaclass to dynamically create bypassers.

    This metaclass is used to dynamically create Bypassers mappings at
    runtime. The Bypassers are special mappings which can be used for
    checking of various variables. To create a Bypassers mapping, you
    need to subclass the Bypassers class.

    In the class body, you can set a few variables that will determine
    how the mapping will behave. These are as follow:

    'values':
                    Iterable of the names of each parameter in the
                    mapping.

        Default:    ("setting",)

    'items':
                    Iterable of 3-tuples which will be checked against
                    when performing various checks. See below.

        Default:    ()

    None of these parameters are mandatory, however, not entering any
    of the above will result in an extremely basic class without much
    functionality. If a parameter is not set, its default value will be
    used. See the classes below for an example.

    It is possible to define the methods that your Bypassers will use,
    however the default methods are made to work with any number of
    arguments, as long as the class body defines the correct arguments.

    """

    allowed = {}
    classes = []

    def __new__(metacls, name, bases, namespace):
        """Create a new Bypassers class."""
        if not any(b in metacls.classes for b in bases):
            metacls.allowed[name] = set(namespace)
            cls = super().__new__(metacls, name, bases, namespace)
            metacls.classes.append(cls)
            return cls

        allowed = metacls.allowed[bases[-1].__name__]

        original = {k:v for k,v in namespace.items() if k in allowed}
        attr = {k:v for k,v in namespace.items() if k not in allowed}

        cls = super().__new__(metacls, name, bases, original)

        cls.attributes = attr
        cls.attributes.setdefault("values", ("setting",))
        cls.attributes.setdefault("items", (("keys", (0,), None),
                                            ("values", (1,), None),
                                            ("items", (0, 1), None)))

        cls.__names__ = tuple(x[0] for x in cls.attributes.get("items"))

        return cls

    def __call__(cls, *names):
        """Create a new Bypassers instance."""

        if cls in cls.__class__.classes:
            raise TypeError("the %s class cannot be called directly" %
                            cls.__name__)

        instance = cls.__new__(cls)

        instance._hashes = []

        mappers = make_sub(cls.__name__, cls.__names__)
        for i, name in enumerate(cls.__names__):
            setattr(instance, name, mappers[i]())

        if isinstance(instance, cls):
            ret = cls.__init__(instance)
            if ret is not None:
                raise TypeError("__init__() should return None, not %r" %
                                ret.__class__.__name__)

        instance.update(*names)

        return instance

    def __repr__(cls):
        """Return a string of itself."""
        return "<bypasser %r>" % cls.__name__

class Bypassers(metaclass=BypassersMeta):
    """Base class to subclass to create Bypassers class.

    This mapping is aimed at emulating a dictionnary, and as such has
    the same methods that a dictionnary has. However, due to the fact
    that this mapping takes exactly five arguments instead of the
    standard one or two, more methods were added, named after standard
    methods from other objects, such as sets and lists. This can be
    subclassed for more functionality.

    Functional API:

    Note: This API provides functionality to allow any of the five
    arguments to be read and modified. If you want to use this
    functional API yourself, you must first read this documentation,
    as some methods do not behave as you would expect them to due to
    the unique nature of this mapping.

    To create the `bypassers` instance, you must call the created class
    with the proper amount of arguments, which differs depending on the
    various implementations.

    bypassers[setting]
                                        Access the internal mapping

    bypassers[setting] = other
                                        Copy a setting's bindings

    del bypassers[setting]
                                        Remove the setting's bindings

    str(bypassers) | repr(bypassers)
                                        Show all the attributes that
                                        are currently active. Note that
                                        the two calls differ

    len(bypassers)
                                        Return the number of settings

    x in bypassers
                                        Return True if x is a setting,
                                        False otherwise

    for x in bypassers
                                        Iterate over all settings in
                                        alphabetical order

    bool(bypassers)
                                        Return True if at least one 
                                        setting is bound, False
                                        otherwise

    dir(bypassers)
                                        Return a list of all methods

    bypassers.extend(iterable)
                                        Add a new binding; need an
                                        iterable, ignored if setting
                                        exists

    bypassers.update(iterable)
                                        Update existing bindings with
                                        iterables or add new bindings

    bypassers.add(setting)
                                        Add new unbound settings,
                                        ignored for existing settings

    bypassers.pop(setting)
                                        Return the iterable bound to
                                        the setting and remove all the
                                        setting's bindings

    bypassers.popitem()
                                        Remove and return a random
                                        binding, five-tuple

    bypassers.get(setting, fallback)
                                        Return the iterable bound to
                                        the setting. If the setting
                                        does not exist, 'fallback' will
                                        be returned; defaults to None

    bypassers.setdefault(item, fb)
                                        Set the default fallback for
                                        setting 'item' to 'fb'; this
                                        only affects .get

    bypassers.count(iters)
                                        Return the number of settings
                                        which are set to use this
                                        (module, attr) pair

    bypassers.copy()
                                        Return a deep copy

    bypassers.clear()
                                        Remove all settings and their
                                        bindings

    Equality testing (== and !=) can be used to compare two different
    instances of the Bypassers mapping. If they have exactly the same
    mapping (same settings bound to the same types, pairs, module and
    attribute), both instances will be considered to be equal. This
    also works even if the other instance is not a Bypassers instance,
    provided they have a similar API. To check if two variables are the
    same instance, use 'is' instead.

    The view objects of this class are changeable. This means that they
    reflect any changes that happened to the mapping. It is also
    guaranteed that the view objects' items will be sorted.

    """

    def __getitem__(self, item):
        """Return the internal mapping of the setting."""
        if item not in self:
            raise KeyError(item)
        return tuple(self.values[self.keys.index(item)])

    def __setitem__(self, item, value):
        """Bind a setting to another setting's bindings."""
        self.update((item, ) + self[value])

    def __delitem__(self, item):
        """Remove the setting and all bindings."""
        if item not in self:
            raise KeyError(item)
        index = self.keys.index(item)
        del self._hashes[index]
        for name in self.__names__:
            del getattr(self, name)[index]

    def __repr__(self):
        """Return a representation of the items in self."""
        args = []
        string = "("
        for name in self.__class__.attributes.get("values"):
            string = string + name + "=%r, "
        string = string[:-2] + ")"
        for binding in self.items():
            args.append(string % binding)
        return "%s(%s)" % (self.__class__.__name__, ", ".join(args))

    def __str__(self):
        """Return a string of the class' items."""
        args = []
        num = len(self.__class__.attributes.get("values")) - 1
        string = "<%s: " + ", ".join(["%s"] * num) + ">"
        for binding in self.items():
            args.append(string % binding)
        return "(" + ", ".join(args) + ")"

    def __iter__(self):
        """Return the special iterator for the Bypassers."""
        return BypassersIterator(self)

    def __len__(self):
        """Return the total number of items in self."""
        return len(self.keys())

    def __dir__(self):
        """Return a list of the methods available."""
        methods = dir(self.__class__)
        methods.remove("attributes")
        return set(methods + list(self.__names__))

    def __contains__(self, item):
        """Return True if item is a setting, False otherwise."""
        return (item in self.keys() and is_hashable(item) and
                self._hashes[self.keys.index(item)] == hash(item))

    def __reversed__(self):
        """Return a reversed iterator."""
        return BypassersIterator(self, reverse=True)

    def __eq__(self, other):
        """Return True if self and other are the same."""
        try:
            if (frozenset(self.items()) == frozenset(other.items()) and
                set(self._hashes) == set(other._hashes)):
                return True
            if frozenset(self) == frozenset(other):
                return True
        except Exception:
            return False
        return False

    def __ne__(self, other):
        """Return True if self and other are not the same."""
        return not (self == other)

    def __lt__(self, other):
        """Return True if self is less than other."""
        if len(self) < len(other):
            return True
        if len(self) > len(other) or self == other:
            return False

        if isinstance(other, type(self)):
            count = 0
            for current, iterator in ((self, other), (other, self)):
                for binding in current.items():
                    if binding[0] not in iterator:
                        count += 1
                        continue
                    rest = binding[1:]
                    for items in iterator[binding[0]]:
                        if items == rest:
                            continue
                        for i, item in enumerate(rest):
                            if items[i] == item:
                                continue
                            if items[i] < item:
                                count += 1
                            else:
                                count -= 1

                count *= -1

            return count < 0

        if hasattr(other, "__iter__") and not hasattr(other, "__next__"):
            count = 0
            for current, iterator in ((self, other), (other, self)):
                for item in current:
                    if item not in iterator:
                        count += 1
                        continue
                count *= -1

            return count < 0

        if hasattr(other, "__iter__") and hasattr(other, "__next__"):
            count = 0
            while True:
                try:
                    item = next(other)
                except StopIteration:
                    break
                if item in self:
                    count -= 1
                else:
                    count += 1

            return count < 0

        return NotImplemented

    def __le__(self, other):
        """Return True if self is equal or less than other."""
        return (self == other) or self.__lt__(other)

    def __ge__(self, other):
        """Return True if self is equal or greater than other."""
        if self.__lt__(other) is NotImplemented:
            return NotImplemented
        return not (self < other)

    def __gt__(self, other):
        """Return True if self is greater than other."""
        if self.__le__(other) is NotImplemented:
            return NotImplemented
        return not (self <= other)

    def __add__(self, value):
        """Return a new instance with new the attributes."""
        return self.copy().__iadd__(value)

    def __radd__(self, value):
        """Return a new instance with the new attributes (reversed)."""
        return self.copy().__iadd__(value)

    def __iadd__(self, value):
        """Update self with the new attributes."""
        if hasattr(value, "items"):
            self.update(*value.items())
            return self

        if hasattr(value, "__iter__") and not hasattr(value, "__next__"):
            self.add(*value)
            return self

        if hasattr(value, "__iter__") and hasattr(value, "__next__"):
            while True:
                try:
                    self.add(next(value))
                except StopIteration:
                    break
            return self

        return NotImplemented

    def __sub__(self, value):
        """Return a new instance without the setting or bindings."""
        return self.copy().__isub__(value)

    def __rsub__(self, value):
        """Remove the attributes in self from value."""
        if hasattr(value, "remove"):
            value = value.copy()
            for item in self:
                if item in value:
                    value.remove(item)
            return value

        if hasattr(value, "__iter__") and not hasattr(value, "__next__"):
            new = []
            for item in value:
                if item not in self:
                    new.append(item)
            return type(value)(new)

        if hasattr(value, "__iter__") and hasattr(value, "__next__"):
            new = []
            while True:
                try:
                    item = next(value)
                except StopIteration:
                    break
                if item not in self:
                    new.append(item)
            return type(value)(new)

        return NotImplemented

    def __isub__(self, value):
        """Remove the settings or bindings from self."""
        if hasattr(value, "items"):
            for items in value.items():
                if items[0] in self and self[items[0]] == tuple(items[1:]):
                    del self[items[0]]
            return self

        if hasattr(value, "__iter__") and not hasattr(value, "__next__"):
            for item in value:
                del self[item]
            return self

        if hasattr(value, "__iter__") and hasattr(value, "__next__"):
            while True:
                try:
                    self.discard(next(value))
                except StopIteration:
                    break
            return self

        return NotImplemented

    def __and__(self, value):
        """Return an iterable of the items both in self and value."""
        return self.copy().__iand__(value)

    def __rand__(self, value):
        """Return an iterable of the items both in self and value."""
        return self.copy().__iand__(value)

    def __iand__(self, value):
        """Update self to only contain items both in self and value."""
        if hasattr(value, "items"):
            for items in value.items():
                if items[0] not in self or self[items[0]] != tuple(items[1:]):
                    self.discard(items[0])
            return self

        if hasattr(value, "__iter__") and not hasattr(value, "__next__"):
            for item in self.keys()[:]:
                if item not in value:
                    del self[item]
            return self

        if hasattr(value, "__iter__") and hasattr(value, "__next__"):
            new = []
            while True:
                try:
                    item = next(value)
                except StopIteration:
                    break
                if item in self:
                    new.append(item)

            self.clear()
            self.update(*new)
            return self

        return NotImplemented

    def __or__(self, value):
        """Return an iterable with items from all iterables."""
        return self.copy().__ior__(value)

    def __ror__(self, value):
        """Return an iterable with items from all iterables."""
        return self.copy().__ior__(value)

    def __ior__(self, value):
        """Update self with items from all iterables."""
        if hasattr(value, "items"):
            for items in value.items():
                self.extend(items)
            return self

        if hasattr(value, "__iter__") and not hasattr(value, "__next__"):
            self.add(*value)
            return self

        if hasattr(value, "__iter__") and hasattr(value, "__next__"):
            while True:
                try:
                    self.add(next(value))
                except StopIteration:
                    break
            return self

    def __xor__(self, value):
        """Return an iterable of all unique items."""
        return self.copy().__ixor__(value)

    def __rxor__(self, value):
        """Return an iterable of all unique items."""
        return self.copy().__ixor__(value)

    def __ixor__(self, value):
        """Update self to keep only the unique items."""
        if hasattr(value, "items"):
            for items in value.items():
                if items[0] in self:
                    self.remove(items[0])
                else:
                    self.extend(items)
            return self

        if hasattr(value, "__iter__") and not hasattr(value, "__next__"):
            for item in frozenset(value):
                if item in self:
                    self.remove(item)
                else:
                    self.add(item)
            return self

        if hasattr(value, "__iter__") and hasattr(value, "__next__"):
            done = []
            while True:
                try:
                    item = next(value)
                except StopIteration:
                    break
                if item in done:
                    continue
                done.append(item)
                if item in self:
                    self.remove(item)
                else:
                    self.add(item)
            return self

        return NotImplemented

    def __pos__(self):
        """Return a deep copy of self."""
        return self.copy()

    def __neg__(self):
        """Remove and return a random item of self."""
        return self.popitem()

    def __invert__(self):
        """Create a new empty bypasser."""
        return self.__class__()

    @property
    def is_bound(self):
        """Return True if at least one setting is bound."""
        args = []
        for mapper, index, handler in self.__class__.attributes.get("items"):
            if handler is not None:
                args.append(getattr(self, mapper)())
        return any(args)

    def update(self, *names):
        """Update the bindings with the given items."""
        items = self.__class__.attributes.get("items")
        for name in names:
            item = (name,)
            if hasattr(name, "items"):
                item = name.items()
            for binding in item:
                binding = list(binding)
                if not is_hashable(binding[0]):
                    raise TypeError("unhashable type: %r" %
                                    type(binding[0]).__name__)
                if binding[0] in self.keys():
                    index = self.keys.index(binding[0])
                    for i, each in enumerate(binding):
                        if each is NoValue:
                            binding[i] = self.items[index][i]
                    for mapper, indexes, handler in items:
                        if handler is NoValue:
                            continue
                        ix = []
                        for i in indexes:
                            if handler is not None:
                                getattr(self, mapper)[index].update(
                                                             binding[i])
                            else:
                                ix.append(binding[i])

                        if handler is None:
                            for m, ind, hndlr in items:
                                if hndlr in (None, NoValue):
                                    continue
                                if set(ind) & set(indexes):
                                    for i in ind:
                                        ix[indexes.index(i)] = getattr(self,
                                                               m)[index]

                        if len(ix) == 1:
                            getattr(self, mapper)[index] = ix[0]
                        elif ix:
                            getattr(self, mapper)[index] = tuple(ix)

                else:
                    index = len(self.keys())
                    self._hashes.append(hash(binding[0]))
                    for mapper, indexes, handler in items:
                        new = []
                        for i in indexes:
                            if handler not in (None, NoValue):
                                binding[i] = handler(binding[i])
                            new.append(binding[i])
                        if len(new) == 1:
                            getattr(self, mapper).append(new[0])
                        elif len(new) > 1:
                            getattr(self, mapper).append(tuple(new))

    def extend(self, items):
        """Add a new full binding."""
        if items[0] in self.keys():
            return
        self.update(items)

    def add(self, *settings):
        """Add new unbound settings. Ignore existing settings."""
        all_settings = []
        for setting in settings:
            if setting in self.keys():
                continue
            lst = [NoValue] * len(self.__class__.attributes.get("values"))
            lst[0] = setting
            all_settings.append(lst)
        self.update(*all_settings)

    def remove(self, item):
        """Remove the setting. Raise KeyError upon failure."""
        del self[item]

    def discard(self, item):
        """Remove the setting if it exists."""
        if item in self:
            del self[item]

    def count(self, iters):
        """Return the number of matching pairs."""
        cnt = 0
        for runner in self.items():
            if runner[-len(iters):] == tuple(iters):
                cnt += 1
        return cnt

    def setdefault(self, item):
        """Set the default fallback for the setting."""
        if item not in self:
            self.add(item)
        return self[item]

    def pop(self, item):
        """Remove and return the bindings of the setting."""
        try:
            return self[item]
        finally:
            self.discard(item)

    def popitem(self):
        """Unbind and return all attributes of a random setting."""
        if not len(self):
            raise KeyError("popitem(): bypasser is empty")
        index = self.keys.index(sorted(self.keys(), key=sorter)[0])
        try:
            return tuple(self.items[index])
        finally:
            del self[self.keys[index]]

    def get(self, item, fallback=None):
        """Return the setting's bindings or fallback."""
        if item not in self:
            return fallback
        return self[item]

    def copy(self):
        """Return a deep copy of self."""
        new = []
        getter = self.__class__.attributes.get
        for binding in self.items():
            binding = list(binding)
            for mapper, indexes, handler in getter("items"):
                for i, name in enumerate(getter("values")):
                    if handler not in (None, NoValue) and i in indexes:
                        binding[i] = binding[i].copy()
            new.append(binding)
        return self.__class__(*new)

    def clear(self):
        """Remove all settings and bindings."""
        try:
            while True:
                self.popitem()
        except KeyError:
            pass

class PairsMapping(BaseMapping):
    """Inner mapping for the pairs argument of the Bypassers."""

    def __init__(self, items):
        """Handle the items properly if None."""
        if items in (None, NoValue):
            items = []
        self._items = items

    def update(self, new):
        """Update the items list with new."""
        if new not in self._items:
            self._items.append(new)

class TypesMapping(BaseMapping):
    """Inner mapping for the types argument of the Bypassers."""

class LevelsMapping(BaseMapping):
    """Inner mapping for the levels argument of the Bypassers."""

class NamesMapping(BaseMapping):
    """Inner mapping for the names argument of the Bypassers."""

class BaseBypassers(Bypassers):
    """Base Bypassers class."""

    values = ("setting", "pairs", "module", "attr")
    items = (("keys",        (0,),           None),
             ("pairs",       (1,),           PairsMapping),
             ("attributes",  (2, 3),         NoValue),
             ("values",      (1, 2, 3),      None),
             ("items",       (0, 1, 2, 3),   None),
            )

class TypeBypassers(Bypassers):
    """Type-based Bypassers class."""

    values = ("setting", "types", "pairs", "module", "attr")
    items = (("keys",       (0,),           None),
             ("types",      (1,),           TypesMapping),
             ("pairs",      (2,),           PairsMapping),
             ("attributes", (3, 4),         NoValue),
             ("values",     (1, 2, 3, 4),   None),
             ("items",      (0, 1, 2, 3, 4),None),
            )

class LevelBypassers(Bypassers):
    """Level-based Bypassers class."""

    values = ("setting", "levels", "pairs", "module", "attr")
    items = (("keys",       (0,),           None),
             ("levels",     (1,),           LevelsMapping),
             ("pairs",      (2,),           PairsMapping),
             ("attributes", (3, 4),         NoValue),
             ("values",     (1, 2, 3, 4),   None),
             ("items",      (0, 1, 2, 3, 4),None),
            )

class NamesBypassers(Bypassers):
    """Names-based Bypassers class."""

    values = ("setting", "names", "levels", "pairs", "module", "attr")
    items = (("keys",       (0,),           None),
             ("names",      (1,),           NamesMapping),
             ("levels",     (2,),           LevelsMapping),
             ("pairs",      (3,),           PairsMapping),
             ("attributes", (4, 5),         NoValue),
             ("values",     (1, 2, 3, 4, 5),None),
             ("items",      (0,1,2,3,4,5),  None),
            )

def get_setting(module, attr, catch=False):
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

# bypass handlers called by the decorator

def check_bypass_base(func, self, *output, **kwargs):
    """Decorator for checking bypassability for the base classes."""
    for setting, pairs, module, attr in self.bypassers.items():
        if module is NoValue or attr is NoValue:
            continue
        for mod, att in pairs:
            if get_setting(mod, att, True):
                self.bypassed[setting] = get_setting(module, attr)
                break

    return func(self, *output, **kwargs)

def check_bypass_type(func, self, *output, type=None, file=None, **rest):
    """Decorator for checking bypassability for the Logger class."""
    if file is type is None:
        type = "normal"
    if type is None:
        for t, f in self.logfiles.items():
            if f == file:
                type = t
                break
        else:
            type = "normal"
    if file is None:
        file = self.logfiles.get(type, self.logfiles["normal"])

    for setting, types, pairs, module, attr in self.bypassers.items():
        if module is NoValue or attr is NoValue:
            continue
        for mod, att in pairs:
            if get_setting(mod, att, True):
                self.bypassed[setting] = get_setting(module, attr)
                break
        else:
            if type in types:
                self.bypassed[setting] = get_setting(module, attr)

    return func(self, *output, type=type, file=file, **rest)

def check_bypass_level(func, self, *output, level=None, file=None, **rest):
    """Decorator for checking bypassability of level-based loggers."""
    if file is None:
        file = self.default_file
    if level is None:
        level = self.default_level
