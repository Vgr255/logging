#!/usr/bin/env python3

"""Implementation of the Bypassers handlers."""

__all__ = ["NoValue"] # the Bypassers get added to this later

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

def extend_index(index, max_len):
    """Extend a tuple of indexes to support Ellipsis."""
    indexes = []
    for i in index:
        if len(indexes) > 1 and indexes[-1] is Ellipsis:
            if hasattr(i, "__index__"):
                indexes.pop()
                indexes.extend(range(indexes[-1], i + 1))
            else:
                raise TypeError("%s cannot be interpreted as an integer" %
                                i.__class__.__name__)

        elif hasattr(i, "__index__"):
            if i < 0:
                i += max_len
            indexes.append(i)

        elif i is Ellipsis:
            if indexes and hasattr(indexes[-1], "__index__"):
                indexes.append(Ellipsis)
            elif not indexes:
                raise IndexError("cannot begin a range by ellipsis")
            else:
                raise TypeError("%s cannot be interpreted as an integer" %
                                indexes[-1].__class__.__name__)

        else:
            raise TypeError("%s cannot be interpreted as an integer" %
                            i.__class__.__name__)

    if indexes and not hasattr(indexes[-1], "__index__"):
        raise TypeError("%s cannot be interpreted as an integer" %
                        indexes[-1].__class__.__name__)

    return indexes

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
        if "NoValue" not in globals():
            nv = super().__new__(meta, cls, bases, clsdict)()
            nv.__class__.__new__ = lambda cls: nv
            return nv
        raise TypeError("type 'NoValue' is not an acceptable base type")

    def __repr__(cls):
        """Return a representation for type(NoValue)."""
        return "<class 'NoValue'>"

class NoValue(metaclass=MetaNoValue):
    """Express the lack of value, as None has a special meaning."""

    def __repr__(self):
        """Return the explicit NoValue string."""
        return "NoValue"

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
            self.__iter__()
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

    In the class body, you need to set a few variables that will
    determine how the mapping will behave. These are as follow:

    'values':
                    Iterable of the names of each parameter in the
                    mapping.

    'items':
                    Iterable of 3-tuples which will be checked against
                    when performing various checks. See below.

    All of the aforementioned parameters are mandatory. If any of
    these are missing, a TypeError will be raised. Any superfluous
    parameter that don't match a method from the base class will be
    silently ignored.

    It is possible to override the behaviour of the base methods from
    the Bypassers class. However, doing so is usually not required, as
    the base methods are made to function with any number of arguments.

    """

    allowed = {}
    classes = dict(base=[], subclass=[], feature=[])

    def __new__(metacls, name, bases, namespace):
        """Create a new Bypassers class."""
        for base in bases:
            if base in metacls.classes["subclass"]:
                raise TypeError("cannot subclass %r" % base.__name__)

        if not any(base in metacls.classes["base"] for base in bases):
            metacls.allowed[name] = set(namespace)
            cls = super().__new__(metacls, name, bases, namespace)
            metacls.classes["base"].append(cls)
            return cls

        for base in bases:
            if base.__name__ in metacls.allowed:
                allowed = metacls.allowed[base.__name__]
                break
        else:
            raise TypeError("no proper base class found")

        original = {k:v for k,v in namespace.items() if k in allowed}
        attr = {k:v for k,v in namespace.items() if k not in allowed}

        if not attr:
            metacls.allowed[name] = set(original)
            cls = super().__new__(metacls, name, bases, original)
            metacls.classes["feature"].append(cls)
            return cls

        for value in ("values", "items"):
            if value not in attr:
                raise TypeError("missing required %r parameter" % value)

        for x in attr["items"]:
            if x[0] in original:
                raise ValueError("name already used: %r")
            if x[0][0] == "_":
                raise ValueError("names cannot start with an underscore")

        cls = super().__new__(metacls, name, bases, original)

        metacls.classes["subclass"].append(cls)

        cls.attributes = attr

        cls.__names__ = tuple(x[0] for x in cls.attributes["items"])

        if name not in globals():
            globals()[name] = cls
        __all__.append(name) # if we got here, it succeeded

        return cls

    def __call__(cls, *names, **keywords):
        """Create a new Bypassers instance."""

        if cls in (cls.__class__.classes["base"] +
                   cls.__class__.classes["feature"]):
            raise TypeError("the %s class cannot be called directly" %
                            cls.__name__)

        if keywords and len(keywords) < len(cls.attributes["values"]):
            raise TypeError("not enough named arguments")
        if len(keywords) > len(cls.attributes["values"]):
            raise TypeError("too many named arguments")

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
        if keywords:
            instance.extend(**keywords)

        return instance

    def __repr__(cls):
        """Return a string of itself."""
        return "<bypasser %r>" % cls.__name__

class Bypassers(metaclass=BypassersMeta):
    """Base class to subclass to create Bypassers class.

    This is a special mapping used for the `bypassers` argument of the
    logger classes. It is constructed using a metaclass, which allows
    basic customization of the behaviour and arguments of the class.
    The methods are taken from the first class created by the metaclass
    in the method resolution order chain. As such, it is possible to
    create new base Bypassers class without subclassing this particular
    class. This class exposes a full functional API, which allows users
    full customization over the instance. There are a few aliases
    for some command available.

    The bypassers retain insertion order, and it is also accessible
    through the external API. To create a new bypasser, it is possible
    to supply an arbitrary number of iterables, that will be passed on
    to the `update` method.

    Note that, while hashing cannot be used for fast lookup of values,
    it is used as a way to ensure the settings are set-like. There can
    only be one of each setting, and they must be hashable. Trying to
    assign a non-hashable variable will result in a TypeError, and the
    mapping will likely be left in a partially-modified state. If, for
    some reason, the hash of a setting changes after it has been
    inserted, it will become unreachable (even though it will still
    occupy space). This can be remedied by iterating over the items,
    re-assigning, or deleting (from the index) such attribute.

    From this point on, `bypasser` will refer to an instance of any
    Bypassers class (a subclass of the present class). It is assumed
    that it was constructed properly. Each method and operation is
    followed by another line, one indent deeper, which states the
    return value of the operation. Unless otherwise stated, a class as
    a return value means that it will return an instance of the
    specified class. A Bypassers instance refers to an instance of any
    subclass. A return value of `bypasser` means that the original
    instance will be returned. A return value of `<...>` means that any
    type may be returned from the method.

    The `bypasser` instance can be created by calling the class, with
    or without iterables, and with or without keyword arguments. If
    passing keyword arguments, this can only affect one setting.

    If overriding methods, please note that `__init__` does not
    actually get any of the passed in arguments; instead, they are
    passed to the `update` (for iterables) and `extend` (for keyword
    arguments) methods, after `__init__` is called. Both the `__new__`
    and `__init__` method will be called without any argument, except
    the class for `__new__` and the instance for `__init__`. Following
    normal Python rules, `__init__` will only be called if `__new__`
    returns an instance of the passed-in class.

    All of the methods are as follow:

    bypasser[n]
                        Get the nth item in insertion order. Raise
                        IndexError if `n` is out of range

        -> tuple

    bypasser[a:b:c]
                        Return a new instance with the items contained
                        in the slice

        -> Bypassers

    bypasser[a, ..., b, c]
                        Return a new instance with the items of the
                        indexes given. A literal `...` means to include
                        every item between `a` and `b`, inclusively

        -> Bypassers

    bypasser[n] = x
                        Set the nth item in insertion order to the
                        items of setting `x`. Raise KeyError if `x` is
                        not a setting

        -> None

    bypasser[a:b:c] = x
                        Set all the items in range(a, b, c) to the
                        items of setting `x`

        -> None

    bypasser[a, ..., b, c] = x
                        Set all the items with the matching indexes to
                        the items of setting `x`

        -> None

    del bypasser[n]
                        Delete the setting at index `n`

        -> None

    del bypasser[a:b:c]
                        Delete all the settings at indexes in
                        range(a, b, c)

        -> None

    del bypasser[a, ..., b, c]
                        Delete all the settings at the indexes given

        -> None

    repr(bypasser)
                        Return a string of the class in the form
                        BypasserClassName((item=value, ...), ...)

        -> str

    str(bypasser)
                        Return a string of the items in the form
                        (<setting: ..., ...>, <...>)

        -> str

    bypasser(x)
                        Retrieve the values associated with the setting
                        `x`. Raise KeyError if `x` is not a setting

        -> tuple

    for x in bypasser | list(bypasser) | iter(bypasser) | ...
                        Return a special iterator used to iterate over
                        the Bypassers instances

        -> BypassersIterator

    len(bypasser)
                        Return the total number of settings currently
                        defined in bypasser

        -> int

    dir(bypasser)
                        Return a list of all methods and non-private
                        instance attributes

        -> list

    x in bypasser
                        Return True if `x` is a setting

        -> bool

    reversed(bypassed)
                        Return a reversed iterator over the items of
                        the bypasser. This uses the same special
                        iterator as iter(bypasser)

        -> BypassersIterator

    bypasser == other
                        Return True if `other` has the same items as
                        bypasser, or at least the same settings

        -> bool

    bypasser != other
                        Same as `not (bypassers == other)`

        -> bool

    bypasser < other
                        Return True if bypasser is considered to be
                        less than `other`. This is done through
                        counting of the various attributes, as well as
                        the total length of both bypasser and `other`

        -> bool

    bypasser <= other
                        Return True if (bypasser < other) or if they
                        have the same length. This is an intentional
                        asymmetry with the `==` operand

        -> bool

    bypasser > other
                        Same as `not (bypasser <= other)`

        -> bool

    bypasser >= other
                        Return True if (bypasser > other) or if they
                        have the same length

        -> bool

    bypasser + other
                        Return a new instance of bypasser with the
                        items from other added

        -> Bypassers

    other + bypasser
                        Same as `bypasser + other`

        -> Bypassers

    bypasser += other
                        Same as `bypasser + other`, except it modifies
                        the instance in-place

        -> bypasser

    bypasser - other
                        Return a new instance of bypasser with the
                        items from other removed, if applicable

        -> Bypassers

    other - bypasser
                        Return a new instance of other, if possible,
                        with the items from bypasser removed, if
                        applicable

        -> type(other)

    bypasser -= other
                        Same as `bypasser - other`, except it modifies
                        the instance in-place

        -> bypasser

    bypasser & other
                        Return a new instance of bypasser which holds
                        the items from both bypasser and `other`

        -> Bypassers

    other & bypasser
                        Same as `bypasser & other`

        -> Bypassers

    bypasser &= other
                        Same as `bypasser & other`, except it modifies
                        the instance in-place

        -> bypasser

    bypasser | other
                        Return an instance of bypasser with the items
                        from both bypasser and `other`. If `other` is
                        a Bypassers instance, the items from bypasser
                        will take precedence over those in `other`, if
                        there's any conflict

        -> Bypassers

    other | bypasser
                        Same as `bypasser | other`

        -> Bypassers

    bypasser |= other
                        Same as `bypasser | other`, except it modifies
                        the instance in-place

        -> bypasser

    bypasser ^ other
                        Return an instance of bypasser with the items
                        from either bypasser or other. Items present in
                        both will not be included

        -> Bypassers

    other ^ bypasser
                        Same as `bypasser ^ other`

        -> Bypassers

    bypasser ^= other
                        Same as `bypasser ^ other`, except it modifies
                        the instance in-place

        -> bypasser

    +bypasser
                        Return a deep copy of bypasser. It is an alias
                        for `bypasser.copy()`

        -> Bypassers

    -bypasser
                        Remove and return a random binding of bypasser.
                        It is an alias for `bypasser.popitem()`,
                        except that it will not raise an exception if
                        bypasser has no item; instead it will return a
                        tuple of `None` items with the same length as
                        a `popitem()` tuple would have. This is to
                        ensure that for loops or other code which
                        expects a specific number of arguments don't
                        fail

        -> tuple

    ~bypasser
                        Return a new, empty instance of bypasser (it
                        does not alter bypasser itself). This is an
                        alias for `type(bypasser)()`

        -> Bypassers

    bypasser.is_bound
                        Boolean value that states whether or not the
                        bypasser instance has bound settings. A setting
                        is considered bound if the third item of the
                        three-tuples given in the `items` parameter has
                        an assigned value at the specified location

        -> bool

    bypasser.ordered
                        Return a (read-only) view of the internal
                        ordering of the settings in the bypasser

        -> tuple

    bypasser.update(iterable, ...)
                        Update the bypasser's mapping with the iterable
                        given. It can accept any number of iterables

        -> None

    bypasser.extend(setting=..., ...=..., ...)
                        Update the bypasser's mapping with the keyword
                        arguments given. This can only affect one
                        setting at a time. It will raise a TypeError if
                        not enough (or too many) parameters are given

        -> None

    bypasser.find(index)
                        Return the setting at index `index`. Raise
                        TypeError if `index` is not an integer. Raise
                        IndexError if `index` is out of range

        -> <...>

    bypasser.index(item)
                        Return the internal index for setting `item`.
                        Raise KeyError if `item` is not a setting

        -> int

    bypasser.add(setting, ...)
                        Add a new, unbound setting. Ignore it if the
                        setting already exists. This can accept any
                        number of settings

        -> None

    bypasser.remove(setting)
                        Remove the setting from bypasser. Raise
                        KeyError if the setting is not present

        -> None

    bypasser.discard(setting)
                        Remove the setting from bypasser. Ignore the
                        operation if the setting is not present

        -> None

    bypasser.count(iterable)
                        Return the number of times `iterable` appears
                        in the bypasser

        -> int

    bypasser.setdefault(item)
                        Return the setting `item` if it exists. If it
                        does not exist, add a new setting `item` and
                        return it

        -> tuple

    bypasser.pop(item)
                        Return the binding of setting `item` if it
                        exists. Raise KeyError if the setting is not
                        present. Remove the setting for bypasser

        -> tuple

    bypasser.popitem()
                        Return a full binding and remove the binding
                        from bypasser. Raise KeyError if `bypasser` is
                        empty. The binding that will be removed is
                        non-random; it will always be the first item
                        when iterating through the bypasser in sorted
                        ordering

        -> tuple

    bypasser.get(item, fallback=None)
                        Return the binding of setting `item` if it
                        exists. If it does not exist, and `fallback` is
                        a tuple, return `fallback`, otherwise return a
                        tuple consisting of n-1 `fallback` items

        -> tuple

    bypasser.copy()
                        Return a deep copy (one layer deep) of bypasser

        -> Bypassers

    bypasser.clear()
                        Remove all existing settings and their bindings

    """

    def __getitem__(self, index):
        """Get the relevant items mapping(s)."""
        if hasattr(index, "__index__"):
            if index < 0:
                index += len(self)
            if index < self:
                return tuple(self.items[index])
            raise IndexError("bypasser index out of range")

        elif isinstance(index, slice):
            return self.__class__(*self.items[index])

        elif isinstance(index, tuple):
            new = ~self
            for i in extend_index(index, len(self)):
                new.update(self[i])
            return new

        else:
            raise TypeError("bypasser indices must be integers, not %s" %
                            index.__class__.__name__)

    def __setitem__(self, index, value):
        """Bind a setting to another setting's bindings."""
        if hasattr(index, "__index__"):
            if index < 0:
                index += len(self)
            if index < self:
                self.update((self.find(index),) + self(value))
            else:
                raise IndexError("bypasser index out of range")

        elif isinstance(index, slice):
            for i in range(*index.indices(len(self))):
                self[i] = value # call itself recursively

        elif isinstance(index, tuple):
            for i in extend_index(index):
                self[i] = value

        else:
            raise TypeError("bypasser indices must be integers, not %s" %
                            index.__class__.__name__)

    def __delitem__(self, index):
        """Remove the setting(s) and all relevant bindings."""
        if hasattr(index, "__index__"):
            if index < 0:
                index += len(self)
            if index < self:
                self.remove(self.find(index))
            else:
                raise IndexError("bypasser index out of range")

        elif isinstance(index, slice):
            items = list(self)
            for i in range(*index.indices(len(self))):
                self.remove(items[i])

        elif isinstance(index, tuple):
            items = list(self)
            for i in extend_index(index):
                self.remove(items[i])

        else:
            raise TypeError("bypasser indices must be integers, not %s" %
                            index.__class__.__name__)

    def __repr__(self):
        """Return a representation of the items in self."""
        args = []
        string = "("
        for name in self.__class__.attributes["values"]:
            string = string + name + "=%r, "
        string = string[:-2] + ")"
        for binding in self.items():
            args.append(string % binding)
        return "%s(%s)" % (self.__class__.__name__, ", ".join(args))

    def __str__(self):
        """Return a string of the class' items."""
        args = []
        num = len(self.__class__.attributes["values"]) - 1
        string = "<%s: " + ", ".join(["%s"] * num) + ">"
        for binding in self.items():
            args.append(string % binding)
        return "(" + ", ".join(args) + ")"

    def __call__(self, item):
        """Return the internal mapping of the setting."""
        if item not in self:
            raise KeyError(item)
        return tuple(self.values[self.index(item)])

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
        length = len(self)
        if length.__lt__(other) is not NotImplemented and length < other:
            return True
        if length.__gt__(other) is not NotImplemented and length > other:
            return False
        if self == other:
            return False
        try:
            if length < len(other):
                return True
            if length > len(other):
                return False
        except TypeError: # no len()
            pass

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
        if self == other:
            return True
        try:
            if len(self) <= other:
                return True
        except TypeError:
            pass
        try:
            if len(self) <= len(other):
                return True
        except TypeError:
            pass
        return self.__lt__(other)

    def __ge__(self, other):
        """Return True if self is equal or greater than other."""
        if self == other:
            return True
        try:
            if len(self) >= other:
                return True
        except TypeError:
            pass
        try:
            if len(self) >= len(other):
                return True
        except TypeError:
            pass
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
                if items[0] in self and self(items[0]) == tuple(items[1:]):
                    self.remove(items[0])
            return self

        if hasattr(value, "__iter__") and not hasattr(value, "__next__"):
            for item in value:
                self.remove(item)
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
                if items[0] not in self or self(items[0]) != tuple(items[1:]):
                    self.discard(items[0])
            return self

        if hasattr(value, "__iter__") and not hasattr(value, "__next__"):
            for item in self[:]:
                if item not in value:
                    self.remove(item)
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
                if items[0] not in self:
                    self.update(items)
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
                    self.update(items)
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
        if self:
            return self.popitem()
        return (None,) * len(self.__class__.attributes["values"])

    def __invert__(self):
        """Create a new empty bypasser."""
        return self.__class__()

    @property
    def is_bound(self):
        """Return True if at least one setting is bound."""
        args = []
        for setting in self:
            for mapper, index, handler in self.__class__.attributes["items"]:
                if handler not in (None, NoValue):
                    for i in index:
                        args.append(self(setting)[i])
        return any(args)

    @property
    def ordered(self):
        """Return the internal ordering of the items."""
        lst = [None] * len(self)
        for item in self:
            lst[self.index(item)] = item
        return tuple(lst)

    def update(self, *names):
        """Update the bindings with the given items."""
        items = self.__class__.attributes["items"]
        for name in names:
            item = (name,)
            if hasattr(name, "items"):
                item = name.items()
            for binding in item:
                binding = list(binding)
                if not is_hashable(binding[0]):
                    raise TypeError("unhashable type: %r" %
                                    type(binding[0]).__name__)
                if binding[0] in self:
                    index = self.index(binding[0])
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
                                for i in (set(ind) & set(indexes)):
                                    ix[indexes.index(i)] = (getattr(self, m)
                                                                    [index])

                        if len(ix) == 1:
                            getattr(self, mapper)[index] = ix[0]
                        elif ix:
                            getattr(self, mapper)[index] = tuple(ix)

                else:
                    index = len(self)
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

    def extend(self, **keywords):
        """Add a new full binding with named pairings."""
        values = self.__class__.attributes["values"]
        if len(keywords) < len(values):
            raise TypeError("not enough parameters given to extend()")
        if len(keywords) > len(values):
            raise TypeError("too many parameters given to extend()")
        lst = [None] * len(values)
        for name, value in keywords.items():
            if name not in values:
                raise ValueError("unrecognized parameter: %r" % name)
            lst[values.index(name)] = value
        self.update(lst)

    def find(self, index):
        """Retrieve the item at location index."""
        if not hasattr(index, "__index__"):
            raise TypeError("bypasser indexes must be integers, not %s" %
                            index.__class__.__name__)
        if index < 0:
            index += len(self)
        if 0 <= index < len(self):
            return self.keys[index]
        raise IndexError("bypasser index out of range")

    def index(self, item):
        """Retrive the internal index for the given item."""
        if item not in self:
            raise ValueError("%s is not in bypasser" % item)
        return self.keys.index(item)

    def add(self, *settings):
        """Add new unbound settings. Ignore existing settings."""
        all_settings = []
        for setting in settings:
            if setting in self:
                continue
            lst = [NoValue] * len(self.__class__.attributes["values"])
            lst[0] = setting
            all_settings.append(lst)
        self.update(*all_settings)

    def remove(self, item):
        """Remove the setting. Raise KeyError upon failure."""
        if item not in self:
            raise KeyError(item)
        self.discard(item)

    def discard(self, item):
        """Remove the setting if it exists."""
        if item not in self:
            return
        index = self.index(item)
        del self._hashes[index]
        for name in self.__names__:
            del getattr(self, name)[index]

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
        return self(item)

    def pop(self, item):
        """Remove and return the bindings of the setting."""
        try:
            return self(item)
        finally:
            self.discard(item)

    def popitem(self):
        """Unbind and return all attributes of a random setting."""
        if not self:
            raise KeyError("popitem(): bypasser is empty")
        index = self.index(sorted(self.keys(), key=sorter)[0])
        try:
            return self[index]
        finally:
            del self[index]

    def get(self, item, fallback=None):
        """Return the setting's bindings or fallback."""
        if item in self:
            return self(item)
        if isinstance(fallback, tuple):
            return fallback
        return (fallback,) * (len(self.__class__.attributes["values"]) - 1)

    def copy(self):
        """Return a deep copy of self."""
        new = []
        for binding in self.items():
            binding = list(binding)
            for m, indexes, handler in self.__class__.attributes["items"]:
                for i, name in enumerate(self.__class__.attributes["values"]):
                    if handler not in (None, NoValue) and i in indexes:
                        binding[i] = binding[i].copy()
            new.append(binding)
        return self.__class__(*new)

    def clear(self):
        """Remove all settings and bindings."""
        while self:
            self.popitem()

class PairsMapping(BaseMapping):
    """Inner mapping for the pairs argument of the Bypassers."""

    def __init__(self, items):
        """Handle the items properly if None."""
        if items in (None, NoValue):
            items = []
        self._items = items

    def update(self, new):
        """Update the items list with new."""
        for item in new:
            if item not in self._items:
                self._items.append(item)

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
