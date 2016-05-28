#!/usr/bin/env python3

# Q: Are you just defining a bunch of methods for the sake of it?
# A: Yes

"""Implementation of the Bypassers handlers."""

import collections
import functools
import copy

from .decorators import Singleton, readonly

__all__ = [] # the Bypassers get added to this later

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

class PartialView(functools.partial):
    """Thin subclass of functools.partial for view objects.

    Unlike types.MethodType (which is not subclassable) or the bare
    functools.partial class, this has a repr which will not clobber
    up the interactive interpreter if the bypasser has a very large
    number of objects. Where `...` is an arbitrary number of items:

    With types.MethodType:
    <bound method __keys__ of BaseBypassers([...])>

    With functools.partial:
    functools.partial(<stable 'keys' view object of 'BaseBypassers'>, BaseBypassers([...]))
    # This exceeds 80 characters even when empty!

    With PartialView:
    <bound view object '__keys__' of 'BaseBypassers'>

    Note: This relies on the C implementation of functools.partial

    """

    def __repr__(self):
        """Return a custom representation of self."""
        return "<bound view object {!r} of {!r}>".format(self.func.__name__,
                                                         self.func.name)

class Viewer: # TODO: set-like methods
    """Return a view object over the items of the instance."""

    def __init__(self, name, value, position, instance):
        self.name = name
        self.value = value
        self.position = position
        self.instance = instance

    def __repr__(self):
        """Return a view of the items."""
        return "{0}{1}([{2}])".format(self.name, self.value.capitalize(),
                                      ", ".join(repr(x) for x in self))

    def __contains__(self, item):
        """Return True if item is in self, False otherwise."""
        for value in self:
            if value == item:
                return True

        return False

    def __iter__(self, factory=iter):
        """Return a modular iterator over the items in the instance."""
        assert factory is iter or factory is reversed
        mapping = self.instance.__mapping__
        item_length = self.instance.__item_length__
        if self.position == (0,): # short-circuit for common use of keys
            if mapping:
                yield from factory(mapping)

        elif self.position == tuple(range(1, item_length)): # common use of values
            for key in factory(mapping):
                if mapping[key]:
                    yield from factory(mapping[key])

        elif self.position == tuple(range(item_length)): # commonly items
            for key in factory(mapping):
                for values in factory(mapping[key]):
                    yield (key, *values)

        else:
            for key in factory(mapping):
                for values in factory(mapping[key]):
                    all_values = (key, *values)
                    concat = []
                    for i in self.position:
                        concat.append(all_values[i])
                    yield tuple(concat)

    def __reversed__(self):
        """Return a reverse iterator over the items in the instance."""
        return self.__iter__(factory=reversed)

    def __eq__(self, other, is_equal=True):
        """Return True if self == other, False otherwise."""
        if self is other:
            return is_equal

        try:
            it = iter(other)
        except TypeError:
            return not is_equal

        if it is other: # 'other' is an iterator: don't exhaust it
            return not is_equal

        for item in self:
            try:
                if item != next(it):
                    return not is_equal
            except StopIteration:
                return not is_equal

        try:
            next(it)
        except StopIteration:
            return is_equal

        return not is_equal

    def __ne__(self, other):
        """Return True if self != other, False otherwise."""
        return self.__eq__(other, is_equal=False)

    def __lt__(self, other):
        """Return True if self < other, False otherwise."""
        if 0 not in self.position:
            return NotImplemented

        if self == other:
            return False

        for item in self:
            try:
                if item not in other:
                    return False
            except TypeError:
                return NotImplemented

        return True

    def __le__(self, other):
        """Return True if self <= other, False otherwise."""
        return self.__lt__(other) or self == other

    def __gt__(self, other):
        """Return True if self > other, False otherwise."""
        value = self.__le__(other)
        if value is NotImplemented:
            return NotImplemented

        return not value

    def __ge__(self, other):
        """Return True if self >= other, False otherwise."""
        return self.__gt__(other) or self == other

class BypassersViewer:
    """Create a view object. This is meant for internal use.

    This class is used to dynamically create the view objects that are
    bound to the various methods on Bypassers classes. This internally
    uses the Viewer class to display the objects when called.

    """

    def __init__(self, sub, index, name):
        """Create a new view object."""
        self.position = index
        self.name = name
        self.__name__ = sub
        self.__doc__ = "Return all the {0} of the {1} class.".format(sub, name)

    def __repr__(self):
        """Return the representation of self."""
        return "<{!r} view object of {!r} objects>".format(self.__name__,
                                                           self.name)

    def __get__(self, instance, owner):
        """Return a bound method of self if an instance is present."""
        self.name = owner.__name__
        if instance is not None:
            return PartialView(self, instance)
        return self

    def __set__(self, instance, value):
        """Prevent overwriting view objects."""
        raise AttributeError("cannot overwrite view object")

    def __delete__(self, instance):
        """Prevent deleting view objects."""
        raise AttributeError("cannot delete view object")

    def __call__(self, instance):
        """Return an iterator over the items in the mapping."""
        return Viewer(self.name, self.__name__, self.position, instance)

class DefaultViews(BypassersViewer):
    """Dedicated subclass for __keys__, __values__ and __items__."""

    def __init__(self, sub, index, name):
        """Create a new default view object."""
        assert sub in ("__keys__", "__values__", "__items__")
        super().__init__(sub, index, name)
        self.__doc__ = "Return the {0} of {1} (stable API).".format(sub[2:-2],
                                                                    name)

    def __repr__(self):
        """Return the representation of self."""
        return "<stable {!r} view object of {!r}>".format(self.__name__[2:-2],
                                                          self.name)

class Subscript:
    """Class for subscription of Bypassers.

    This class will be returned by a subscript to a Bypassers class if the
    subscript is a 'str', 'bytes', 'tuple' or the Ellipsis ('...') singleton.

    This is used to dynamically return the items, reflecting changes to the
    original mapping. This is also used to allow modifications to the mapping
    through subsequent indexing.

    """

    def __init__(self, instance, item):
        """Create a new subscript object for the Bypassers."""
        self.instance = instance
        self.item = item

    def __getitem__(self, position):
        """Return the item at the position given."""
        if isinstance(position, slice):
            pass

        elif not hasattr(position, "__index__"):
            raise TypeError("position must be an integer or slice")

    def __len__(self):
        """Return the length of self."""
        return len(self.instance)

    def __repr__(self):
        """Return a representation of self."""
        return "<subscript {0} of {1}>".format(self.item, type(self.instance).__name__)

    def __iter__(self, factory=iter):
        """Yield all items of self in order."""
        assert factory is iter or factory is reversed
        inst = self.instance
        mapping = inst.__mapping__
        item = self.item
        if isinstance(item, (str, bytes)):
            yield from factory(mapping[item])

        elif isinstance(item, tuple):
            done = set()
            for setting in factory(item):
                if isinstance(setting, (str, bytes)) and setting in mapping:
                    if setting not in done:
                        yield from factory(mapping[setting])
                        done.add(setting)

                elif hasattr(setting, "__index__"):
                    try:
                        key = inst._get_setting(setting)
                    except IndexError:
                        continue

                    if key not in done:
                        yield from factory(mapping[key])
                        done.add(key)

                elif isinstance(setting, slice):
                    start, stop, step = setting.indices(len(mapping))
                    if setting.step is None:
                        step = factory is iter or -1
                    elif factory is reversed and step > 0:
                        raise ValueError("reversed() with non-negative step is unsupported")

                    for position in range(start, stop, step):
                        try:
                            key = inst._get_setting(position)
                        except IndexError:
                            continue

                        if key not in done:
                            yield from factory(mapping[key])
                            done.add(key)

                elif setting is Ellipsis:
                    for key in mapping:
                        if key not in done:
                            yield from factory(mapping[key])
                            done.add(key)

        elif item is Ellipsis:
            for setting in factory(mapping):
                for values in factory(mapping[setting]):
                    yield (setting, *values)

    def __reversed__(self):
        """Yield all items in reverse order."""
        return self.__iter__(factory=reversed)

class BypassersMeta(type):
    """Metaclass to dynamically create bypassers.

    This metaclass is used to dynamically create Bypassers mappings at
    runtime. The Bypassers are special mappings which can be used for
    checking of various variables. To create a Bypassers mapping, you
    need to subclass the Bypassers class.

    In the class body, you need to set a few variables that will
    determine how the mapping will behave. These are as follow:

    '__names__':
                    Iterable of the names of each parameter in the
                    mapping.

    '__views__':
                    Iterable of 2-tuples which will be checked against
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

    def __new__(meta, name, bases, namespace):
        """Create a new Bypassers class."""
        for base in bases:
            if base.__name__ not in meta.allowed:
                raise TypeError("cannot subclass {!r}".format(base.__name__))

        if name == "Bypassers" and namespace["__module__"] == __name__:
            meta.allowed[name] = set(namespace)
            return super().__new__(meta, name, bases, namespace)

        for base in bases:
            if base.__name__ in meta.allowed:
                allowed = meta.allowed[base.__name__]
                break
        else:
            raise TypeError("no proper base class found")

        attr = {k:v for k,v in namespace.items() if k not in allowed}

        if not attr:
            meta.allowed[name] = set(namespace)
            cls = super().__new__(meta, name, bases, namespace)
            return cls

        for value in ("__names__", "__views__"):
            if value not in attr:
                raise TypeError("missing required {!r} parameter".format(value))

        for x in attr["__views__"]:
            if x[0] in namespace:
                raise ValueError("{!r}: name already exists".format(x[0]))
            if x[0].startswith("_"):
                raise ValueError("names cannot start with an underscore")

        for item in ("__item_length__", "__viewers__"):
            if item in namespace:
                raise ValueError("member {!r} is reserved for internal use")

        cls = super().__new__(meta, name, bases, namespace)

        cls.__item_length__ = len(attr["__names__"])
        cls.__viewers__ = tuple(x[0] for x in attr["__views__"])

        tup = tuple(range(cls.__item_length__))

        for sub, pos in cls.__views__:
            setattr(cls, sub, BypassersViewer(sub, pos, name))

        cls.__keys__ = DefaultViews("__keys__", tup[0], name)
        cls.__values__ = DefaultViews("__values__", tup[1:], name)
        cls.__items__ = DefaultViews("__items__", tup, name)

        if cls.__module__ == __name__:
            __all__.append(name) # if we got here, it succeeded

        return cls

    def __repr__(cls):
        """Return a string of itself."""
        return "<bypasser {!r}>".format(cls.__name__)

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

    """

    @readonly
    def __mapping__(self):
        """Underlying OrderedDict mapping."""

    def __new__(cls, names=None):
        """Create a new bypasser instance."""
        if cls in type(cls).allowed:
            raise TypeError("cannot instantiate the {!r} class".format(cls.__name__))

        return super().__new__(cls)

    def __init__(self, names=None):
        """Initialize the instance."""
        self.__mapping__ = collections.OrderedDict()

        if names is not None:
            self.update(names)

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

    def __getitem__(self, item):
        """Return the items based on the input."""
        if hasattr(item, "__index__"):
            return self._get_setting(item)

        elif isinstance(item, slice):
            new = type(self)()
            new_mapping = new.__mapping__
            mapping = self.__mapping__
            for position in range(*item.indices(len(mapping))):
                try:
                    key = self._get_setting(position)
                except IndexError:
                    continue
                else:
                    new_mapping[key] = mapping[key]
            return new

        elif isinstance(item, (str, bytes, tuple)) or item is Ellipsis:
            return Subscript(self, item)

        raise TypeError("{!r} is not a supported input".format(type(item).__name__))

    def __delitem__(self, item):
        """Delete some parts of the bypasser."""
        mapping = self.__mapping__
        if isinstance(item, (str, bytes)):
            del mapping[item]

        elif hasattr(item, "__index__"):
            if item < 0:
                item += len(mapping)
            if 0 <= item < len(mapping):
                for i, setting in enumerate(mapping):
                    if i == item:
                        del mapping[setting]
                        break

            else:
                raise IndexError("bypasser index out of bounds")

        elif isinstance(item, tuple):
            if Ellipsis in item:
                mapping.clear()
            else:
                to_remove = set()
                for setting in item:
                    if isinstance(setting, (str, bytes)) and setting in mapping:
                        to_remove.add(setting)

                    elif hasattr(setting, "__index__"):
                        try:
                            to_remove.add(self._get_setting(setting))
                        except IndexError:
                            pass

                    elif isinstance(setting, slice):
                        for position in range(*setting.indices(len(mapping))):
                            try:
                                to_remove.add(self._get_setting(position))
                            except IndexError:
                                pass

                for setting in to_remove:
                    del mapping[setting]

        elif isinstance(item, slice):
            to_remove = set()
            for position in range(*item.indices(len(mapping))):
                to_remove.add(self._get_setting(position))
            for setting in to_remove:
                del mapping[setting]

        elif item is Ellipsis:
            mapping.clear()

    def __repr__(self):
        """Accurate representation of self."""
        mapping = self.__mapping__
        return "{0}([{1}])".format(self.__class__.__name__,
               ", ".join(str(x) for x in ((k, *v) for k in mapping for v in mapping[k])))

    def __eq__(self, other):
        """Return True if self and other are equivalent, False otherwise."""
        return self.__mapping__ == getattr(other, "__mapping__", None)

    def __ne__(self, other):
        """Return False if self and other are equivalent, True otherwise."""
        return not (self == other)

    def __copy__(self):
        """Return a shallow copy of self."""
        new = self.__new__(type(self))
        new.__mapping__ = self.__mapping__.copy()
        return new

    def __deepcopy__(self, memo):
        """Return a deep copy of self."""
        new = type(self)()
        new_mapping = new.__mapping__
        for key, values in self.__mapping__.items():
            new_mapping[key] = copy.deepcopy(values, memo)
        return new

    def _get_setting(self, index):
        """Get the item at index given."""
        assert hasattr(index, "__index__")
        mapping = self.__mapping__
        index = int(index)
        if index < 0:
            index += len(mapping)
        if 0 <= index < len(mapping):
            for i, setting in enumerate(mapping):
                if i == index:
                    return setting

        raise IndexError("bypasser index out of bounds")

    def _update_from_list_or_tuple(self, list_or_tuple):
        """Update the bypasser with list or tuple."""
        assert isinstance(list_or_tuple, (list, tuple))
        length = len(list_or_tuple)
        item_length = self.__item_length__
        mapping = self.__mapping__
        if length == item_length:
            setting = list_or_tuple[0]
            if not isinstance(setting, (str, bytes)):
                raise TypeError("setting must be str or bytes")

            if setting not in mapping:
                mapping[setting] = []
            mapping[setting].append(tuple(list_or_tuple[1:]))

        elif length > item_length:
            raise ValueError("too many items in list or tuple (expected "
                             "{0}, got {1})".format(item_length, length))

        else:
            raise ValueError("not enough items in list or tuple (expected "
                             "{0}, got {1})".format(item_length, length))

    def _update_from_mapping(self, mapping):
        """Update the bypasser with a mapping."""
        for key in mapping:
            if not isinstance(key, (str, bytes)):
                raise TypeError("setting must be str or bytes")

            for value in mapping[key]:
                if isinstance(value, (list, tuple)):
                    self._update_from_list_or_tuple(value)

                elif isinstance(value, dict): # not only because it's too complicated, but because it doesn't make sense
                    raise TypeError("cannot parse nested dicts")

                elif isinstance(value, Bypassers):
                    raise TypeError("cannot parse nested Bypassers instance")

                else:
                    self._update_from_iterable(value)

    def _update_from_iterable(self, iterable):
        """Update the bypasser with any sort of iterable."""
        mapping = self.__mapping__

        try:
            it = iter(iterable)
        except TypeError:
            raise TypeError("non-iterable data passed to update()") from None

        try:
            setting = next(it)
        except StopIteration:
            raise ValueError("empty iterable passed to update()") from None

        if not isinstance(setting, (str, bytes)):
            raise TypeError("setting must be str or bytes")

        data = []

        for i in range(1, self.__item_length__):
            try:
                data.append(next(it))
            except StopIteration:
                raise ValueError("not enough items in iterable (expected "
                      "{0}, got {1})".format(self.__item_length__, i)) from None

        try:
            next(it)
        except StopIteration:
            pass
        else:
            raise ValueError("too many items in iterable (expected "
                             "{0})".format(self.__item_length__))

        if setting not in mapping:
            mapping[setting] = []
        mapping[setting].append(tuple(data))

    @staticmethod
    def _prevent_wrong_input(data):
        """Raise according errors for bad input."""
        if isinstance(data, (set, frozenset)):
            raise TypeError("no order defined for sets and frozen sets")

        elif isinstance(data, (str, bytes, bytearray, memoryview)):
            raise TypeError("cannot use str or bytes-like object as iterable")

    def update(self, iterable_of_iterables):
        """Update the bindings with the given items.

        The parameters can be any number of another Bypassers instance,
        but that instance must have the same item length, or else a
        ValueError will be raised.

        The most common way to update the Bypassers is to call it with
        a list or tuple of the proper size.

        Using a set or frozenset instance is explicitly disallowed, as
        parsing it would become ambigous regarding the order. Using
        unicode (str) or a bytes-like object (bytes, bytearray and
        memoryview) make no sense, and are more likely to be a mistake,
        as the 'add' method requires only single arguments, not
        iterables.

        Any other form of iterable, including generators and user-defined
        collections, are allowed. This method is guarded against infinite
        iterators such as 'itertools.count()' and will simply error out in
        such cases.

        A regular dict may also be used, even though the keys' order is not
        consistent, as sometimes ordering doesn't matter as much. An instance
        of 'collections.OrderedDict' can also be used in this fashion. The
        restrictions on the values are the same as for the rest, where lists
        and tuples are most common, and set, frozenset, str, bytes, bytearray
        and memoryview instances are disallowed. Moreover, dict and Bypassers
        instances are disallowed as well, as it makes no sense to use those as
        iterables for values.

        This method is the building ground for most other methods, which
        rely on it.

        """

        # don't attempt to throw everything in a list right away
        # this helps have finer-grained error messages
        # if there are too many items, it won't spend extra time/memory building a useless list
        # and if it's infinite, it will simply error out instead of hanging forever
        mapping = self.__mapping__
        for name in iterable_of_iterables:
            self._prevent_wrong_input(name)

            if isinstance(name, Bypassers):
                if name.__item_length__ == self.__item_length__:
                    for key in name:
                        if key not in mapping:
                            mapping[key] = []
                        for values in name.__mapping__[key]:
                            mapping[key].append(values)
                else:
                    raise ValueError("Bypassers instance with unmatching length")

            elif isinstance(name, dict):
                self._update_from_mapping(name)

            elif isinstance(name, (tuple, list)): # fast path
                self._update_from_list_or_tuple(name)

            else: # slow path for user-defined classes
                self._update_from_iterable(name)

    def add(self, *names):
        """Add unbound settings."""
        mapping = self.__mapping__
        values = self.__names__[1:] # don't count setting
        for name in names:
            if isinstance(name, (str, bytes)):
                data = []
                for value, default in values:
                    if default in (None, NoValue):
                        data.append(default)
                    else:
                        data.append(default())

                if name not in mapping:
                    mapping[name] = []
                mapping[name].append(tuple(data))

            else:
                raise TypeError("setting must be str or bytes")

    def copy(self, *, deep=False):
        """Return a deep or shallow copy of self, defaulting to shallow."""
        if deep:
            return type(self).__deepcopy__(self, {})
        return type(self).__copy__(self)

    def clear(self):
        """Remove all items from the Bypasser."""
        self.__mapping__.clear()

    def to_dict(self, *, ordered=True):
        """Return a dict (or OrderedDict) of self."""
        if ordered:
            return self.__mapping__.copy()
        return dict(self.__mapping__)

    def to_list(self):
        """Return a list of the items in self."""
        mapping = self.__mapping__
        return [(key, *values) for key in mapping for values in mapping[key]]

    @classmethod
    def from_iterable(cls, iterable):
        """Create a new instance from an iterable."""
        cls._prevent_wrong_input(iterable)
        self = cls()
        if iterable is None:
            pass # allow None to be a simple class creation
        elif isinstance(iterable, (list, tuple)):
            self._update_from_list_or_tuple(iterable)
        else:
            self._update_from_iterable(iterable)
        return self

    @classmethod
    def from_mapping(cls, mapping):
        """Create a new instance from a mapping."""
        cls._prevent_wrong_input(mapping)
        self = cls()
        if mapping is not None:
            self._update_from_mapping(mapping)
        return self

class BaseBypassers(Bypassers):
    """Base Bypassers class."""

    __names__ = (("setting",    NoValue),
                 ("pairs",      set    ),
                 ("module",     None   ),
                 ("attr",       str    ),
                )

    __views__ = (("keys",        (0,)        ),
                 ("pairs",       (1,)        ),
                 ("attributes",  (2, 3)      ),
                 ("values",      (1, 2, 3)   ),
                 ("items",       (0, 1, 2, 3)),
                )

class NumberMethods:
    """Dummy class for number methods."""

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
                self = self.copy(deep=True)
            for setting in other:
                if setting in self:
                    self.__mapping__.move_to_end(setting, last=(not reversed))
                for values in other[setting]:
                    self.update((setting, *values))

            return self

        return NotImplemented

    def __sub__(self, other):
        """Return a new instance with all items but those in other."""
        return self.__isub__(other, copy=True)

    def __rsub__(self, other):
        """Return a new instance with all items but those in other."""
        return self.__isub__(other, copy=True)

    def __isub__(self, other, copy=False):
        """Remove all items present in other from self."""
        if hasattr(other, "__mapping__"):
            if copy:
                self = self.copy(deep=True)
            for setting in other:
                if setting in self:
                    if False: pass # temporary so the code runs

NOTES = """

__mapping__     DONE    underlying OrderedDict mapping
__item_length__ DONE    number of items in the Bypasser
__attr__        DONE    class-level attributes
__names__       DONE    view object names

__new__         DONE    create a new instance and prevent illegal instantiation
__init__        DONE    initialize the instance

__iter__        DONE    iter(bypasser) -> iterator of settings
__reversed__    DONE    reversed(bypasser) -> reversed iterator of settings

__repr__        DONE    repr(bypasser) -> BypasserClass(["setting", {"types"}, (None, "pairs"), "module", "attr"], [...])
__str__                 str(bypasser) -> [(setting="setting", types={"types"}, pairs=(...), module=..., attr=...), (...)]

__format__              format(bypasser, format_spec) -> various representations based on format_spec (same as repr() if empty)

__eq__          DONE    bypasser == other -> True if they have the same items, False otherwise
__ne__          DONE    bypasser != other -> not (bypasser == other)
__lt__
__gt__
__le__
__ge__
<, >, >=, <= -> set-like comparisons

__len__         DONE    len(bypasser) -> number of settings

__dir__         DONE    dir(bypasser) -> methods and view objects | DEFAULT IMPLEMENTATION

__setattr__     DONE    prevent creating new instance variables
__delattr__     DONE    prevent deleting anything from the instance

__getitem__
        SINGLE STR DONE bypasser["setting"] -> return a list of everything bound to this setting

        SINGLE INT DONE bypasser[42] -> return the setting at index, raise IndexError if not present

                        this returns the *setting* at the position; to get the value, use bypasser[42,]

        TUPLE   DONE    bypasser["setting1", "setting2", ...] -> list of everything bound to all settings

                        ints may also be used, but then the *list* will be returned with the rest, not the setting

                        this ignores non-existent settings (so bypasser["no-setting",] will swallow the KeyError)

        SLICE   DONE    bypasser[start:stop:step] -> return a list of all settings from the internal ordering

                        this returns the *settings*, like regular ints

                        normal slicing rules apply

        ELLIPSIS DONE   bypasser[...] (Ellipsis) -> list everything bound (no setting)

__setitem__
        SINGLE STR      bypasser["setting"] = x -> rename the setting to x

        SINGLE INT      bypasser[42] = x -> change the internal index of the setting, moving all others up/down according, raise IndexError if not present

        TUPLE           bypasser["setting1", "setting2", ...] = x -> merge all items from all settings into this one, renaming it to x

        SLICE           bypasser[start:stop:step] = x -> merge all items from the locations into x

        ELLIPSIS        bypasser[...] = x -> merge every setting into setting x

__delitem__
        SINGLE STR      del bypasser["setting"] -> remove all bindings of 'setting'; raise KeyError if not present

        SINGLE INT      del bypasser[42] -> remove the setting at index, moving accordingly; raise IndexError if not present

        TUPLE           del bypasser["setting1", "setting2", ...] -> remove all bindings of all settings; ignore if not present

        SLICE           del bypasser[start:stop:step] -> delete settings and bindings at relevant indexes

        ELLIPSIS        del bypasser[...] (Ellipsis) -> delete everything

__call__                <undefined>

__contains__    DONE    x in bypasser -> True if x is a setting, False otherwise

Implementation detail: For every magic binary operation, their reversed equivalent and the in-place ones, only the in-place one should have the logic; the others should call it

__add__                 bypasser + other -> Add all settings from other into bypasser, order matching other's
__radd__                other + bypasser -> Add all settings from other into bypasser, order matching bypasser's
__iadd__                bypasser += other -> in-place __add__
__sub__                 bypasser - other -> Remove all bypasser settings present in other
__rsub__                other - bypasser -> Remove all 'other' items present as bypasser setting
__isub__                bypasser -= other -> in-place __sub__
__mul__                 bypasser * other -> Run all items pairs through the function 'other', a tuple is passed as sole argument
__rmul__                other * bypasser -> identical behaviour
__imul__                bypasser *= other -> in-place __mul__
__pow__                 bypasser ** other -> Run all items pairs through the function 'other', all items are passed as single arguments
__rpow__                other ** bypasser -> identical behaviour
__ipow__                bypasser **= other -> in-place __pow__
__truediv__             bypasser / other -> Return an instance with settings having less than 'other' items
__rtruediv__            other / bypasser -> identical behaviour
__itruediv__            bypasser /= other -> in-place __truediv__
__floordiv__            bypasser // other -> Return an instance with settings having more than 'other' items
__rfloordiv__           other // bypasser -> identical behaviour
__ifloordiv__           bypasser //= other -> in-place __floordiv__
__matmul__              bypasser @ other -> Return an instance with settings having exactly 'other' items
__rmatmul__             other @ bypasser -> identical behaviour
__imatmul__             bypasser @= other -> in-place __matmul__
__mod__                 bypasser % other -> Add the iterable to a new instance; same as bypasser.copy().update(it)
__rmod__                other % bypasser -> Identical behaviour
__imod__                bypasser %= other -> in-place __mod__
__rshift__              bypasser >> other -> Move all settings one position right; wrapping around
__rrshift__             other >> bypasser -> Same as bypasser << other
__irshift__             bypasser >>= other -> in-place __rshift__
__lshift__              bypasser << other -> Move all settings one position left; wrapping around
__rlshift__             other << bypasser -> Same as bypasser >> other
__ilshift__             bypasser <<= other -> in-place __lshift__
__and__                 bypasser & other -> all settings and their parameters that appear all the time
__rand__                other & bypasser -> identical behaviour
__iand__                bypasser &= other -> in-place __and__
__xor__                 bypasser ^ other -> all settings with their parameters that appear only once
__rxor__                other ^ bypasser -> identical behaviour
__ixor__                bypasser ^= other -> in-place __xor__
__or__                  bypasser | other -> all settings and everything else
__ror__                 other | bypasser -> identical behaviour
__ior__                 bypasser |= other -> in-place __or__

__neg__                 -bypasser -> return a bypasser with all settings, but no bound
__pos__                 +bypasser -> return a copy of the bypasser
__invert__              ~bypasser -> return a new empty bypasser

with bypasser as x:
    Same as:
    x = bypasser
    try:
        ... do whatever ...
    except Exception:
        pass

__enter__
__exit__

bypasser.update DONE    -> Update the mapping with the provided iterables
bypasser.extend         -> Update with keyword arguments ???
bypasser.index          -> Find the internal index of a setting; raise IndexError if not present
bypasser.find           -> Get the setting at index given; return -1 if not present
bypasser.count          -> How many times the setting is used
bypasser.clear          -> Clears the whole bypasser
bypasser.copy   DONE    -> Returns a copy of the bypasser
bypasser.insert         -> Inserts data into setting ???
bypasser.move           -> Move setting into position
bypasser.pop            -> Remove an arbitrary setting
bypasser.popitem        -> Remove a random setting
bypasser.add    DONE    -> Add a new empty setting
bypasser.drop           -> Remove the setting and all bindings at position x; ignore if not present; x defaults to 0
bypasser.get            -> Get the data bound to setting or a tuple consisting of n items
bypasser.strip          -> Remove all settings that are not bound
bypasser.sort           -> Sort all keys

bypasser.to_enum
bypasser.to_dict DONE (+ ordered keyword for an OrderedDict)
bypasser.to_list DONE

Bypassers.from_enum
Bypassers.from_mapping
Bypassers.from_iterable

"""
