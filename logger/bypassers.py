#!/usr/bin/env python3

# Q: Are you just defining a bunch of methods for the sake of it?
# A: Yes

"""Implementation of the Bypassers handlers."""

import collections
import types
import enum

from .decorators import (

    Singleton,
    readonly,

)

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

class Viewer: # TODO: set-like methods
    """Return a view object over the items of the instance."""

    def __init__(self, name, value, position, instance):
        self.name = name
        self.value = value
        self.position = position
        self.instance = instance

    def __repr__(self):
        """Return a view of the items."""
        return "{0}{1}([{2}])".format(self.name, self.value.title(),
                                      ", ".join(repr(x) for x in self))

    def __contains__(self, item):
        """Return True if item is in self, False otherwise."""
        for value in self:
            if value == item:
                return True

        return False

    def __iter__(self, factory=iter):
        """Return a modular iterator over the items in the instance."""
        mapping = self.instance.__mapping__
        item_length = self.instance.__item_length__
        if self.position == (0,): # short-circuit for common use of keys
            if mapping:
                yield from factory(mapping)

        elif self.position == tuple(range(1, item_length+1)): # common use of values
            for key in factory(mapping):
                if mapping[key]:
                    yield from factory(mapping[key])

        elif self.position == tuple(range(item_length+1)): # commonly items
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

    def __eq__(self, other):
        """Return True if self == other, False otherwise."""
        try:
            it = iter(other)
        except TypeError:
            return False

        for item in self:
            try:
                if item != next(it):
                    return False
            except StopIteration:
                return False

        try:
            next(it)
        except StopIteration:
            return True

        return False

    def __ne__(self, other):
        """Return True if self != other, False otherwise."""
        try:
            it = iter(other)
        except TypeError:
            return True

        for item in self:
            try:
                if item != next(it):
                    return True
            except StopIteration:
                return True

        try:
            next(it)
        except StopIteration:
            return False

        return True

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
        if 0 not in self.position:
            return NotImplemented

        if self == other:
            return True

        return self.__lt__(other)

    def __gt__(self, other):
        """Return True if self > other, False otherwise."""
        value = self.__le__(other)
        if value is NotImplemented:
            return NotImplemented

        return not value

    def __ge__(self, other):
        """Return True if self >= other, False otherwise."""
        if 0 not in self.position:
            return NotImplemented

        if self == other:
            return True

        return self.__gt__(other)

class CreateViewer:
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
        self.name = owner.__name__
        if instance is not None:
            return types.MethodType(self, instance)
        return self

    def __set__(self, instance, value):
        raise AttributeError("cannot overwrite view object")

    def __delete__(self, instance):
        raise AttributeError("cannot delete view object")

    def __call__(self, instance):
        """Return an iterator over the items in the mapping."""
        return Viewer(self.name, self.__name__, self.position, instance)

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

        original = {k:v for k,v in namespace.items() if k in allowed}
        attr = {k:v for k,v in namespace.items() if k not in allowed}

        if not attr:
            meta.allowed[name] = set(original)
            cls = super().__new__(meta, name, bases, original)
            meta.classes["feature"].append(cls)
            return cls

        for value in ("values", "items"):
            if value not in attr:
                raise TypeError("missing required {!r} parameter".format(value))

        for x in attr["items"]:
            if x[0] in original:
                raise ValueError("{!r}: name already exists".format(x[0]))
            if x[0].startswith("_"):
                raise ValueError("names cannot start with an underscore")

        cls = super().__new__(meta, name, bases, original)

        meta.classes["subclass"].append(cls)

        cls.__attr__ = attr
        cls.__item_length__ = len(attr["values"])
        cls.__names__ = tuple(x[0] for x in attr["items"])

        for sub, pos, _ in attr["items"]:
            setattr(cls, sub, CreateViewer(sub, pos, name))

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

    def __new__(cls, *names):
        """Create a new bypasser instance."""
        if cls is Bypassers or cls in type(cls).classes["feature"]:
            raise TypeError("cannot instantiate the {!r} class".format(
                                                                cls.__name__))

        return super().__new__(cls)

    def __init__(self, *names):
        """Initialize the instance."""
        self.__mapping__ = collections.OrderedDict()

        self.update(*names)

    def __get__(self, instance, owner):
        """Bind the instance to self."""
        return self

    def __set__(self, instance, value):
        """Prevent changing the value of the bypasser."""
        raise AttributeError("cannot change value of bypasser")

    def __delete__(self, instance):
        """Prevent deleting the bypasser from an instance."""
        raise AttributeError("cannot delete a bypasser")

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

    def __hash__(self):
        """Return a constant hash of self."""
        return id(self)

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

    def __call__(self, index):
        """Return the setting at index given."""
        if not hasattr(index, "__index__"):
            raise TypeError("bypasser indexes must be integers, "
                            "not {0}".format(index.__class__.__name__))

        if index < 0:
            index += len(self)
        if 0 <= index < len(self):
            for i, setting in enumerate(self):
                if i == index:
                    return setting
        raise IndexError("bypasser index out of range")

    def __reduce__(self):
        """Return information for pickling."""
        return self.__reduce_ex__(self, 2)

    def __reduce_ex__(self, proto):
        """Tool for advanced pickling."""
        return self.__class__, tuple(self.items())

    def __copy__(self):
        """Return a shallow copy of self."""
        return self.__class__(*self.items())

    def __deepcopy__(self, memo):
        """Return a deep copy of self."""
        new = self.__class__() # still todo

    def __setattr__(self, item, value):
        """Prevent creation of invalid variables."""
        if item not in dir(self):
            raise AttributeError("cannot create instance variable "
                                 "{!r}".format(item))
        super().__setattr__(item, value)

    def __delattr__(self, item):
        """Disallow deleting instance variables."""
        raise AttributeError("cannot delete instance variable "
                             "{!r}".format(item))

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
                self = self.copy(deepcopy=True)
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
                self = self.copy(deepcopy=True)
            for setting in other:
                if setting in self:
                    if False: pass # temporary so the code runs

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
        #items = self.__class__.attributes["items"]
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

    def update(self, *names):
        """Update the bindings with the given items."""
        items = self.__attr__["items"]
        mapping = self.__mapping__
        for name in names:
            assert isinstance(name, (list, tuple)), "only list and tuple supported for now"
            if len(name) == self.__item_length__:
                setting = name[0]
                if setting not in self:
                    mapping[setting] = []
                mapping[setting].append(tuple(name[1:]))
            else:
                raise ValueError("wrong length")

    def copy(self, *, deepcopy=False):
        """Return a deep or shallow copy of self, defaulting to shallow."""
        if deepcopy:
            return self.__deepcopy__({})
        return self.__copy__()

    def clear(self):
        """Remove all items from the Bypasser."""
        self.__mapping__.clear()

class BaseBypassers(Bypassers):
    """Base Bypassers class."""

    values = ("setting", "pairs", "module", "attr")
    items = (("keys",        (0,),           None),
             ("pairs",       (1,),           None),
             ("attributes",  (2, 3),         NoValue),
             ("values",      (1, 2, 3),      None),
             ("items",       (0, 1, 2, 3),   None),
            )











NOTES = """

__mapping__     DONE    underlying OrderedDict mapping
__item_length__ DONE    number of items in the Bypasser
__attr__        DONE    class-level attributes
__names__       DONE    view object names

__new__         DONE    create a new instance and prevent illegal instantiation
__init__        DONE    initialize the instance

__get__         DONE    get the instance and class
__set__         DONE    set a new value to the bypasser
__delete__      DONE    delete the bypasser

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
        SINGLE STR      bypasser["setting"] -> return a list of everything bound to this setting

        SINGLE INT      bypasser[42] -> return the setting at index, raise IndexError if not present

        TUPLE           bypasser["setting1", "setting2", ...] -> list of everything bound to all settings

                        this ignores non-existent settings (so bypasser["no-setting",] will swallow the KeyError)

        SLICE           bypasser[start:step:stop] -> return a list of all settings from the internal ordering

                        normal slicing rules apply

        ELLIPSIS        bypasser[...] (Ellipsis) -> list everything bound (no setting)

__setitem__
        SINGLE STR      bypasser["setting"] = x -> rename the setting to x

        SINGLE INT      bypasser[42] = x -> change the internal index of the setting, moving all others up/down according, raise IndexError if not present

        TUPLE           bypasser["setting1", "setting2", ...] = x -> merge all items from all settings into this one, renaming it to x

        SLICE           bypasser[start:stop:end] = x -> merge all items from the locations into x

        ELLIPSIS        bypasser[...] = x -> merge every setting into setting x

__delitem__
        SINGLE STR      del bypasser["setting"] -> remove all bindings of 'setting'; raise KeyError if not present

        SINGLE INT      del bypasser[42] -> remove the setting at index, moving accordingly; raise IndexError if not present

        TUPLE           del bypasser["setting1", "setting2", ...] -> remove all bindings of all settings; ignore if not present

        SLICE           del bypasser[start:stop:index] -> delete settings and bindings at relevant indexes

        ELLIPSIS        del bypasser[...] (Ellipsis) -> delete everything

__call__        DONE    bypasser(index) -> return the setting at index

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

bypasser.update         -> Update the mapping with the provided iterables
bypasser.extend         -> Update with keyword arguments ???
bypasser.index          -> Find the internal index of a setting; raise IndexError if not present
bypasser.find           -> Get the setting at index given; return -1 if not present
bypasser.count          -> How many times the setting is used
bypasser.clear          -> Clears the whole bypasser
bypasser.copy           -> Returns a copy of the bypasser
bypasser.insert         -> Inserts data into setting ???
bypasser.move           -> Move setting into position
bypasser.pop            -> Remove an arbitrary setting
bypasser.popitem        -> Remove a random setting
bypasser.add            -> Add a new empty setting
bypasser.remove         -> Remove setting at position x; raise KeyError or IndexError if not present; x defaults to 0
bypasser.discard        -> Remove setting at position x; ignore if not present; x defaults to 0
bypasser.erase          -> Remove the setting and all bindings at position x; raise KeyError or IndexError if not present; x defaults to 0
bypasser.drop           -> Remove the setting and all bindings at position x; ignore if not present; x defaults to 0
bypasser.get            -> Get the data bound to setting or a tuple consisting of n items
bypasser.strip          -> Remove all settings that are not bound
bypasser.sort           -> Sort all keys

bypasser.to_enum
bypasser.to_dict
bypasser.to_ordered_dict
bypasser.to_list

Bypassers.from_enum
Bypassers.from_mapping
Bypassers.from_ordered_mapping
Bypassers.from_iterable

"""
