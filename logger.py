"""Improved Logger module by Vgr v0.1
Documentation string still to-do."""

"""Notes:
Here are notes for what this module should be able to do.
These are here since this module is not complete yet

- Ability to write to screen as well as one or more files
- Per-line setting to decide whether to display or not, and to write or not
- Logging levels (like error, debug, etc)
- Need a way to call Logger("hello world") to make it print right away
- This could be done through subclassing
- Needs a way to be fed a dict of {logtype:file} pairs
- Needs a way to be fed arbitrary parameters to the class instance
- Subclassing should allow one to do anything with the subclass (almost)

The default print function was completely remade.
It can safely override the built-in print() function

Timestamps are properly implemented.
This has the ability to split cleverly on long lines.

Next to-do:
- Make the logger() method, to do proper all-around logging
- Implement a way to bypass some settings
- Implement arbitrary string replacing from within another module (translating)
- Add ability to view docstrings properly (already implemented elsewhere)
"""

from datetime import datetime
import shutil
import time
import sys

class NoValue:
    """Used to express the lack of value as None can be a value."""

    def __repr__(self):
        return 'NoValue'

    def __bool__(self):
        return False

NoValue = NoValue()

class Container:
    """Base container class for printing arguments."""

    def __init__(self, items):
        """Create a new items set."""
        self._items = items

    def __iter__(self):
        """Return an iterator over the items of self."""
        return iter(self._items)

    def __len__(self):
        """Return the amount if items in self."""
        return len(self._items)

    def __contains__(self, item):
        """Return True if item is in self."""
        return item in self._items

    def __repr__(self):
        """Return a string of all items."""
        return "%s(%s)" % (self.__class__.__name__,
               ", ".join(repr(item) for item in sorted(self._items)))

    def __eq__(self, other):
        """Return True if self and other are identical, False otherwise."""
        if hasattr(other, "_items") and self._items == other._items:
            return True
        return False

    def __ne__(self, other):
        """Return True if self and other are not identical, True otherwise."""
        if not hasattr(other, "_items") or self._items != other._items:
            return True
        return False

_mappers = {}

for sub in ("Keys", "Values", "Items", "Types", "Pairs", "Attributes"):
    _map_doc = """Return all the %s of the class.""" % sub.lower()
    _mappers[sub.lower()] = type("Bypassers" + sub, (Container,),
                                {'__doc__': _map_doc})

class BaseMapping(Container):
    """Lightweight class for inner iteration."""

    def __call__(self):
        """Return self to trigger __repr__()."""
        return self

    def add(self, item):
        """Add a new item to the set."""
        self._items.add(item)

    def remove(self, item):
        """Remove an item from the set."""
        self._items.remove(item)

    def update(self, new):
        """Update the set with new."""
        self._items.update(new)

class TypesMapping(BaseMapping):
    """Subclass for the Types argument."""

class PairsMapping(BaseMapping):
    """Subclass for the Pairs argument."""

class InnerMapping(Container):
    """Special mapping used by the Bypassers class for types and pairs."""

    def __init__(self, iters=([], [])):
        """Create a new inner iterable."""
        self.types = TypesMapping(iters[0])
        self.pairs = PairsMapping(iters[1])

    def __iter__(self):
        """Return an iterator over types and pairs."""
        return iter((self.types, self.pairs))

    def __len__(self):
        """Return the total lenght of types and pairs."""
        return len(self.types) + len(self.pairs)

    def __contains__(self, item):
        """Return True if item is in self, False otherwise."""
        return item in self.types or item in self.pairs

    def __repr__(self):
        """Return a representation of the types and pairs."""
        return "%s(types=%s, pairs=%s)" % (self.__class__.__name__, 
                                            self.types, self.pairs)

class Bypassers(Container):
    """Special mapping used by the bypassers argument of the Logger class.

    This mapping is aimed at emulating a dictionnary, and as such has the same
    methods that a dictionnary has. However, due to the fact this mapping takes
    exactly five arguments instead of the standard one or two, more methods
    were added, named after standard methods from other objects, such as sets
    and lists. This can be subclassed for more functionality.

    Functional API:

    Notes: This API provides functionality to allow any of the five arguments
    to be read and modified. If you want to use this functional API yourself,
    you must first read this documentation, as some actions do not behave as
    they would be normally expected due to the unique nature of this mapping.

    bypassers = Bypassers((setting, [types], [(module, attr)], module, attr))

    bypassers[setting]                  Access the internal mapping of types
                                        and pairs

    del bypassers[setting]              Remove the setting and all bindings

    bypassers[setting].types            Access the internal mapping of types

    bypassers[setting].types.add(type)  Add a new type

    bypassers[setting].types.remove(t)  Remove an existing type

    bypassers[setting].pairs            Access the internal mapping of pairs

    bypassers[setting].pairs.add(pair)  Add a new (module, attr) pair

    bypassers[setting].pairs.remove(p)  Remove an existing (module, attr) pair

    bypassers[setting].types()          Same API as bypassers[setting].types

    bypassers[setting].pairs()          Same API as bypassers[setting].pairs

    str(bypassers) | repr(bypassers)    Show all the settings, types, pairs,
                                        modules and attributes currently active

    len(bypassers)                      Return the total amount of settings

    x in bypassers                      Return True if x is a setting, whether
                                        bound or not; False otherwise

    for x in bypassers                  Iterate over all settings

    bool(bypassers)                     Return True if at least one setting is
                                        bound, False otherwise

    dir(bypassers)                      Return a list of all methods

    bypassers.extend(iterable)          Add a new binding; need a five-tuple

    bypassers.update(iterable)          Update an existing binding with a
                                        five-tuple; setting must exist

    bypassers.add(setting)              Add a new unbound setting

    bypassers.pop(setting)              Return the (types, pairs, module,
                                        attr) iterable bound to setting and
                                        removes all the setting's bindings.

    bypassers.popitem()                 Remove and return a random pair of
                                        (setting, types, pairs, module, attr)

    bypassers.get(setting, fallback)    Return the (types, pairs, module,
                                        attr) iterable bound to the setting. If
                                        the setting does not exist, 'fallback'
                                        will be returned; defaults to None.

    bypassers.setdefault(item, fb)      Set the default fallback for setting
                                        'item' to 'fb'; this only affects .get

    bypassers.count(iters)              Return the number of settings which
                                        are set to use this (module, attr) pair

    bypassers.keys()                    Return all existing settings

    bypassers.values()                  Return all (types, pairs, module,
                                        attr) tuples currently active

    bypassers.items()                   Return all existing five-tuples

    bypassers.types()                   Return all types

    bypassers.pairs()                   Return all pairs

    bypassers.read()                    Return all (module, attr) pairs

    bypassers.copy()                    Return a new instance with the same
                                        attributes.

    bypassers.clear()                   Remove all bindings

    Equality testing (== and !=) can be used to compare two different instances
    of the Bypassers mapping. If they have exactly the same mapping (same
    settings bound to the same types, pairs, module and attribute), both
    instances will be considered to be equal. This also works even if the other
    instance is not a Bypassers instance, provided they have an identical API.
    To check if two variables are the same instance, use 'is' instead.
    """

    def __init__(self, *names):
        """Create a new instance of the class."""
        self._items = {}
        self.fallbacks = {}
        for setting, types, pairs, module, attr in names:
            self._items[setting] = [InnerMapping((types, pairs)), module, attr]

    def __getitem__(self, item):
        """Return the internal mapping of the setting."""
        return self._items[item][0]

    def __delitem__(self, item):
        """Remove the setting and all its bindings."""
        del self._items[item]

    def __bool__(self):
        """Return True if at least one setting is bound."""
        for item in self._items:
            if self._items[item][0]:
                return True
        return False

    def __repr__(self):
        """Return a string of all active attributes."""
        args = []
        for setting, ((types, pairs), module, attr) in self._items.items():
            args.append("(setting=%r, types=%r, pairs=%r, module=%r, attr=%r)"
                       % (setting, types, pairs, module, attr))
        return '%s(%s)' % (self.__class__.__name__, " | ".join(args))

    def __dir__(self):
        """Return a list of all methods of the class."""
        return dir(self.__class__)

    def update(self, new):
        """Update the setting's bindings."""
        setting, types, pairs, module, attr = new
        self._items[setting][0].types.update(types)
        self._items[setting][0].pairs.update(pairs)
        if module is NoValue:
            module = self._items[setting][1]
        if attr is NoValue:
            attr = self._items[setting][2]
        self._items[setting][1:] = [module, attr]

    def extend(self, items):
        """Add a new binding of (setting, types, pairs, module, attr)."""
        setting, types, pairs, module, attr = items
        self._items[setting] = [InnerMapping((types, pairs)), module, attr]

    def add(self, setting):
        """Add a new unbound setting. Ignored if setting exists."""
        if setting in self._items:
            return
        self._items[setting] = [InnerMapping(), NoValue, NoValue]

    def pop(self, item):
        """Remove and return the bindings of setting."""
        (types, pairs), module, attr = self._items.pop(item)
        return (types, pairs, module, attr)

    def popitem(self):
        """Unbinds and returns all attributes of a random setting."""
        setting, ((types, pairs), module, attr) = self._items.popitem()
        return (setting, types, pairs, module, attr)

    def get(self, item, fallback=NoValue):
        """Return the settings' bindings, or fallback if not available."""
        if item not in self._items:
            if item in self.fallbacks and fallback is NoValue:
                fallback = self.fallbacks[item]
            return fallback
        (types, pairs), module, attr = self._items[item]
        return (types, pairs, module, attr)

    def setdefault(self, item, fallback=None):
        """Set the default fallback for the get() method."""
        self.fallbacks[item] = fallback
        if fallback is NoValue:
            del self.fallbacks[item]

    def count(self, iters):
        """Return the amount of (module, attr) bindings in all settings."""
        cnt = 0
        module, attr = iters
        for mod, att in self.read():
            if mod == module and att == attr:
                cnt += 1
        return cnt

    def keys(self):
        """Return all settings, bound or otherwise."""
        return _mappers["keys"](self._items)

    def values(self):
        """Return all values."""
        reader = []
        for (types, pairs), module, attr in self._items.values():
            reader.append((types, pairs, module, attr))
        return _mappers["values"](reader)

    def items(self):
        """Return all existing five-tuples."""
        reader = []
        for setting, ((types, pairs), module, attr) in self._items.items():
            reader.append((setting, types, pairs, module, attr))
        return _mappers["items"](reader)

    def types(self):
        """Return all types."""
        reader = []
        for (types, pairs), module, attr in self._items.values():
            reader.append(types)
        return _mappers["types"](reader)

    def pairs(self):
        """Return all pairs."""
        reader = []
        for (types, pairs), module, attr in self._items.values():
            reader.append(pairs)
        return _mappers["pairs"](reader)

    def read(self):
        """Return all (module, attr) tuples."""
        reader = []
        for inner, module, attr in self._items.values():
            reader.append((module, attr))
        return _mappers["attributes"](reader)

    def copy(self):
        """Return a new instance with the same attributes."""
        new = []
        for setting, ((types, pairs), module, attr) in self._items.items():
            new.append((setting, types, pairs, module, attr))
        return self.__class__(*new)

    def clear(self):
        """Remove all settings and their bindings."""
        self._items.clear()

class LoggerMeta(type):
    """Metaclass for the Logger classes.

    The base class' docstring carries over to all subclasses.
    """

    def __new__(metacls, cls, bases, classdict):
        """Generate the new classes with concatenated docstrings."""
        newcls = type.__new__(metacls, cls, bases, classdict)
        if not hasattr(metacls, "_all"):
            metacls._all = {}
        metacls._all[cls] = newcls
        if not hasattr(metacls, "base"): # care only about the base class
            newcls._is_base = True
            metacls.base = newcls
            metacls.basedoc = newcls.__doc__
            if metacls.basedoc is None:
                metacls.basedoc = ""
        else: # handle subclassing properly
            newcls._is_base = False
            for somecls in metacls._all.values():
                if newcls in somecls.__subclasses__():
                    col = shutil.get_terminal_size()[0]
                    newdoc = somecls.__doc__ + "\n\n\n"
                    if newcls.__doc__:
                        newcls.__doc__ = newdoc + newcls.__doc__
                    else:
                        newcls.__doc__ = somecls.__doc__
        return newcls

class BaseLogger(metaclass=LoggerMeta):
    r"""Base Logger class for your everyday needs.

    This uses the LoggerMeta metaclass to handle subclassing.
    This can be inherited to create custom classes.
    This is not user-faced. For general purposes, please use the Logger class.

    Usage: BaseLogger(
           sep = " ",
           ending = "\n",
           file = None,
           use_utc = False,
           ts_format = "[%Y-%m-%d] (%H:%M:%S UTC{tzoffset})",
           )

    sep:            String to be used to join the lines together.

        Default:    " "

    ending:         String to be appended at the end of the lines.

        Default:    "\n"

    file:           Default file to use for anything (both for printing to
                    screen and writing to a file). This should not be altered
                    when instantiating the class and be left None.

        Default:    None

    use_utc:        Boolean value to determine whether timestamps should use
                    Universal Coordinated Time or the local time.

        Default:    False

    ts_format:      Format string for timestamps. The parameters are the same
                    as the time module's 'strftime' method. However, for the
                    time zone name and offset, use {tzname} and {tzoffset}
                    respectively. This is done to account for the use_utc
                    parameter as well as allow full cross-platformity (some
                    platforms, such as certain versions of Windows, fail to
                    interpret %z properly). The timezone name will be the
                    uppercased three-letters abbreviation. The time zone offset
                    is a string with + or - following by 4 digits, like +0000
                    or -0500, the digits being HHMM.

        Default:    "[%Y-%m-%-d] (%H:%M:%S UTC{tzoffset})"
    """

    def __init__(self, sep=" ", ending="\n", file=sys.stdout, use_utc=False,
                 ts_format="[%Y-%m-%d] (%H:%M:%S UTC{tzoffset})"):

        self.separator = sep
        self.ending = ending
        self.file = file

        self.use_utc = use_utc

        # this can have {tzname} and {tzoffset} for formatting
        # this adds respectively a timezone in the format UTC or EST
        # and an offset from UTC in the form +0000 or -0500
        self.ts_format = ts_format

    def _get_timestamp(self, use_utc=None, ts_format=None):
        """Return a timestamp with timezone + offset from UTC."""
        if use_utc is None:
            use_utc = self.use_utc
        if ts_format is None:
            ts_format = self.ts_format
        if use_utc:
            tmf = datetime.utcnow().strftime(ts_format)
            tz = "UTC"
            offset = "+0000"
        else:
            tmf = time.strftime(ts_format)
            tz = time.tzname[0]
            offset = "+"
            if datetime.utcnow().hour > datetime.now().hour:
                offset = "-"
            offset += str(time.timezone // 36).zfill(4)
        return tmf.format(tzname=tz, tzoffset=offset).strip().upper() + " "

    def _split_lines(self, out, sep=" ", end="\n"):
        """Split long lines at clever points to avoid weird clipping."""
        col = shutil.get_terminal_size()[0]
        if not isinstance(out, str):
            out = sep.join(out) # make any iterable work
        out = out.strip(" ")
        lines = out.split("\n")
        splines = [line.split() for line in lines]
        newlines = [] # newline-separated lines
        for i, line in enumerate(lines):
            if len(line) <= col:
                newlines.append(line)
                continue
            newstr = ""
            for word in splines[i]:
                if newstr:
                    new = " ".join((newstr, word))
                else:
                    new = word
                if len(new) > col:
                    newlines.append(newstr)
                    newstr = word
                else:
                    newstr = new
            if newstr:
                newlines.append(newstr)
        return newlines

    # this is the re-implementation of the built-in print function
    # we use this later for printing to screen
    # we can override the default function in the outer scope
    def _print(self, *output, file=None, sep=None, end=None, split=True):
        """Print to screen or file in a safer way.

        This mimics the built-in print() behaviour and adds versatility.
        This can be used directly, or tweaked for additional functionality."""

        if file is None:
            file = self.file

        if sep is None:
            sep = self.separator

        if end is None:
            end = self.ending

        if split:
            output = self._split_lines(output, sep, end)

        # create a file object handler to write to.
        # if 'file' has a write() method, don't ask questions and use it
        # it's up to the end user if that method fails
        if hasattr(file, "write"):
            objh = file
        else:
            # if a str or bytes, assume it's a file
            # otherwise, assume stdout or similar
            if isinstance(file, (str, bytes)):
                objh = open(file, "a", errors="replace")
            else: # likely int
                objh = open(file, "w", errors="replace", closefd=False)

        objh.write(sep.join(output) + end) # mimic built-in print() behaviour

        # instead of asking for it, flush the stream if we can
        if hasattr(objh, "flush"):
            objh.flush()

        # close the used resources if we can, again no need to ask for it
        # however, make sure sys.stdout is NOT closed
        if hasattr(objh, "close") and objh not in (sys.stdout, sys.stderr):
            objh.close()

    def _get_output(self, out, sep, end):
        """Sanitize output and joins iterables together."""
        if not out: # called with no argument, let's support it anyway
            out = ['']
        msg = None
        for line in out:
            if isinstance(line, (list, tuple)):
                line = sep.join(line)
            if msg is None:
                msg = line
            else:
                if line == "":
                    line = "\n"
                msg = msg + sep + str(line)
        return msg + end

class Logger(BaseLogger):
    """Main Logger class for general and specific logging purposes.

    This is inherited from the BaseLogger class.

    The options are the same as the base class, with these additions:

    display:        Default parameter to determine if the loggers should
                    print to screen. This can be overriden on a per-call basis.

        Default:    True

    write:          Default parameter to determine if the loggers should
                    write to a file. This can be overriden on a per-call basis.

        Default:    True

    logfiles:       Dictionary of {type:file} pairs. The type is the logging
                    type that the logger expects. The file is the file that
                    tells the logger to write to. This can be used for dynamic
                    file logging.

        Default:    {"normal": "logger.log"}

    bypassers:      Iterable of (setting, types, module, attr) iterables. Do
                    note that 'types' is an iterable of all types that can
                    match this bypassers. 'setting' is the setting to bypass
                    when at least one of the types matches the type that the
                    logger was called with. It will replace the setting's value
                    with the value of attribute 'attr' of module or dict
                    'module'. If 'module' is None, 'attr' will be used as its
                    immediate value, without any other lookup.

        Default:    () - Converted to a dynamic instance at runtime
    """

    def __init__(self, separator=" ", ending="\n", file=None, use_utc=False,
                 ts_format="[%Y-%m-%d] (%H:%M:%S UTC{tzoffset})", write=True,
                 display=True, logfiles={}, bypassers=()):

        BaseLogger.__init__(self, separator, ending, file, use_utc, ts_format)

        self.display = display
        self.write = write

        self.logfiles = {"normal": "logger.log"}
        self.logfiles.update(logfiles)

        # this needs to be list/tuple of (setting, types, pairs, module, attr)
        # tuples; the setting is the setting to bypass; types is a list of
        # types to check for to determine if bypassing should occur, same
        # about the pairs, except for module/attr matches; module and attr are
        # used with getattr() to bypass the value of setting with the one found
        # in the given module, for the given attribute; module of None means
        # to use the attr as the direct value; making the type None will also
        # indicate that any type can be triggered. to indicate a lack of value
        # for any parameter, pass NoValue as None has a special meaning
        # for starters, prepare 'ignorers'
        self.bypassers = Bypassers(("timestamp", set(), set(), NoValue, NoValue),
                                   ("splitter", set(), set(), NoValue, NoValue),
                                   ("all", set(), set(), NoValue, NoValue))

        self.bypassers.update(bypassers)

    def logger(self, *output, file=None, type=None, display=None, write=None,
               sep=None, end=None, split=True, use_utc=None, ts_format=None):
        """Log everything to screen and/or file. Always use this."""
        if sep is None:
            sep = self.separator

        if end is None:
            end = self.ending

        if display is None:
            display = self.display

        if write is None:
            write = self.write

        if file is type is None:
            type = "normal"

        if type is None:
            for f, t in self.logfiles.items():
                if f == file:
                    type = t
                    break
            else:
                type = "normal"

        if file is None:
            file = self.logfiles.get(type, self.logfiles["normal"])

        output = self._get_output(output, sep, end)
        timestamp = self._get_timestamp(use_utc, ts_format)
        # todo
