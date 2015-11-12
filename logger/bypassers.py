#!/usr/bin/env python3

"""Implementation of the Bypassers handlers."""

import collections
import types
import enum

from .decorators import attribute, DescriptorProperty, Singleton

__all__ = ["NoValue"] # the Bypassers get added to this later

def get_id(x):
    value = object.__repr__(x)
    return value[value.rindex("0x"):-1]

def is_dunder(name):
    """Return True if a __dunder__ name, False otherwise."""
    return name[:2] == name[-2:] == "__" and "_" not in (name[2:3], name[-3:-2])

def sorter(x):
    # this is very ugly and I am not pleased with it, so if anyone can
    # come up with a better solution, I'm all open
    # see http://bugs.python.org/issue20630 and
    #     http://bugs.python.org/issue20632
    """Make sure non-string objects are last."""
    if "__lt__" not in type(x).__dict__:
        return "????????"
    if not isinstance(x, str):
        return "????" + str(x).lower()
    return x.lower()

def convert_to_od(mapping, order):
    """Convert mapping to an OrderedDict instance using order."""
    return collections.OrderedDict([(i, mapping[i]) for i in order])

@Singleton
class NoValue:
    """Express the lack of value, as None has a special meaning."""

    def __repr__(self):
        """Return the explicit NoValue string."""
        return "NoValue"

    def __bool__(self):
        """Return False no matter what."""
        return False

class Viewer:
    """Return a view object over the items of the instance."""

    def __init__(self, name, value, position, instance):
        self.name = name
        self.value = value
        self.position = position
        self.instance = instance

    def __repr__(self):
        """Return a view of the items."""
        return "%s(%s)" % (self.name, [repr(x) for x in self])

    def __len__(self):
        """Return the number of items self will return."""
        return len(self.instance)

    def __iter__(self):
        """Return a modular iterator over the items in the instance."""
        mapping = self.instance.__mapping__
        if self.position == (0,): # short-circuit for common use of keys
            if mapping:
                yield from mapping

        elif self.position == tuple(range(1, len(self))): # common use of values
            for key in mapping:
                if mapping[key]:
                    yield from mapping[key]

        elif self.position == tuple(range(len(self))): # commonly items
            for key in mapping:
                for values in mapping[key]:
                    yield (key, *values)

        else:
            for key in mapping:
                for values in mapping[key]:
                    all_values = (key, *values)
                    concat = []
                    for i in self.position:
                        concat.append(all_values[i])
                    yield tuple(concat)

class CreateViewer:
    """Create a view object."""

    instance = None
    owner = object
    name = "<unknown>"

    def __init__(self, sub, index):
        """Create a new view object."""
        self.value = sub
        self.position = index

    @DescriptorProperty
    def __doc__(self, cls):
        if self is None:
            return "Create a view object."
        return "Return all the %s of the %s class." % (self.value, self.name)

    def __repr__(self):
        """Return the representation of self."""
        if self.instance is None:
            return "<%r view object of %r objects>" % (self.value, self.name)
        return "<bound view object %r of %r objects at %s>" % (self.value, self.name, get_id(self))

    def __get__(self, instance, owner):
        self.instance = instance
        self.owner = owner
        self.name = owner.__name__
        return self

    def __call__(self, *args):
        """Return an iterator over the items in the mapping."""
        if args and self.instance is not None or len(args) > 1:
            raise TypeError("%s() takes no arguments (%i given)" % (self.value, len(args) - 1))
        if not args and self.instance is None:
            raise TypeError("descriptor %r of %r object needs an argument" % (self.value, self.name))
        if args:
            instance = args[0]
        else:
            instance = self.instance
        if not isinstance(instance, self.owner):
            raise TypeError("descriptor %r requires a %r object but received a %r" %
                            (self.value, self.name, type(instance).__name__))

        return Viewer(self.name, self.value, self.position, instance)

Bypassers = NoValue # temporary value until it is created

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
    classes = dict(subclass=[], feature=[])

    def __new__(meta, name, bases, namespace):
        """Create a new Bypassers class."""
        for base in bases:
            if base in meta.classes["subclass"]:
                raise TypeError("cannot subclass %r" % base.__name__)

        if Bypassers is NoValue and name == "Bypassers":
            meta.allowed[name] = set(namespace)
            return super().__new__(meta, name, bases, namespace)

        for base in bases:
            if base.__name__ in meta.allowed:
                allowed = meta.allowed[base.__name__]
                break
        else:
            raise TypeError("no proper base class found")

        original = {k:v for k,v in namespace.items() if k in allowed}
        attr = {k:v for k,v in namespace.items() if k not in allowed}

        if not attr:
            meta.allowed[name] = set(original)
            cls = super().__new__(meta, name, bases, original)
            meta.classes["feature"].append(cls)
            return cls

        for value in ("values", "items"):
            if value not in attr:
                raise TypeError("missing required %r parameter" % value)

        for x in attr["items"]:
            if x[0] in original:
                raise ValueError("%r: name already exists" % x[0])
            if x[0].startswith("_"):
                raise ValueError("names cannot start with an underscore")
            if not x[0].islower():
                raise ValueError("names must be lowercased")

        if not {"keys", "values", "items"} < set(x[0] for x in attr["items"]):
            raise ValueError("need at least 'keys', 'values', and 'items'")

        cls = super().__new__(meta, name, bases, original)

        meta.classes["subclass"].append(cls)

        cls.__attr__ = attr

        cls.__item_length__ = len(attr["values"])

        cls.__names__ = tuple(x[0] for x in attr["items"])

        for sub, pos, _ in attr["items"]:
            setattr(cls, sub, CreateViewer(sub, pos))

        if cls.__module__ == __name__:
            __all__.append(name) # if we got here, it succeeded

        return cls

    def __call__(cls, names=NoValue):
        """Create a new Bypassers instance."""

        if cls is Bypassers or cls in cls.__class__.classes["feature"]:
            raise TypeError("the %s class cannot be called directly" %
                            cls.__name__)

        self = cls.__new__(cls)

        self.__mapping__ = collections.OrderedDict()

        if isinstance(self, cls):
            ret = cls.__init__(self)
            if ret is not None:
                raise TypeError("__init__() should return None, not %r" %
                                ret.__class__.__name__)

        if names is not NoValue:
            self.update(*names)

        return self

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

    """

    @attribute
    def __mapping__(self):
        """Underlying OrderedDict mapping."""

    def __iter__(self):
        """Iterate over the items of self."""
        yield from self.__mapping__

    def __reversed__(self):
        """Iterate over the items of self in reverse order."""
        yield from reversed(self.__mapping__)

    def __len__(self):
        """Return the length of self."""
        return len(self.__mapping__)

    def __contains__(self, item):
        """Return True if item is in self, False otherwise."""
        return item in self.__mapping__

    def __repr__(self):
        """Accurate representation of self."""
        display = []
        for key in self.__mapping__:
            for values in self.__mapping__[key]:
                display.append((key, *values))
        return "%s(%s)" % (self.__class__.__name__, display)

    def __eq__(self, other):
        """Return True if self and other are equivalent, False otherwise."""
        return self.__mapping__ == getattr(other, "__mapping__", None)

    def __ne__(self, other):
        """Return False if self and other are equivalent, True otherwise."""
        return not (self == other)

    def __dir__(self):
        """Return a list of all methods and attributes."""
        names = set(dir(self.__class__))
        return names - {"attributes"} | self.__names__

    def __call__(self, index):
        """Return the setting at index given."""
        if not hasattr(index, "__index__"):
            raise TypeError("bypasser indexes must be integers, not %s" %
                            index.__class__.__name__)

        if index < 0:
            index += len(self)
        if 0 <= index < len(self):
            for i, setting in enumerate(self):
                if i == index:
                    return setting
        raise IndexError("bypasser index out of range")

    def __add__(self, other):
        """Return a new instance with settings from other."""
        return self.__iadd__(other, copy=True)

    def __radd__(self, other):
        """Return a new instance with settings from other (reversed)."""
        return self.__iadd__(other, reversed=True, copy=True)

    def __iadd__(self, other, reversed=False, copy=False):
        """Add all settings from other into self."""
        if hasattr(other, "__mapping__"):
            if copy:
                self = self.copy()
            for setting in other:
                if setting in self:
                    self.__mapping__.move_to_end(setting, last=(not reversed))
                for values in other[setting]:
                    self.update((setting, *values))

        # XXX TODO

    # The following is the OLD CODE of the update method!
    # It does NOT work with the current implementation
    # Do NOT attempt to tackle this code while tired or otherwise less able to code
    # This function holds the wisdom of many late nights spent debugging
    # It may seem arcane, but every bit of it is NEEDED
    # With the new implementation, if you don't end up with a method which
    # is AT LEAST almost as long as this one, you're doing it wrong
    # It's a pain, and probably that most of the code doesn't even work anymore
    # Thankfully, code doesn't rust, and may still be recycled
    # It is the most important method of this class, it must be done right
    # At least 15 different test cases will be needed to cover this one method

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

