# Advanced logging module for various purposes
# Copyright (C) 2015 Emanuel 'Vgr' Barry
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Improved Logger module by Vgr v0.1
Documentation string still to-do."""

"""Notes:
Here are notes for what this module should be able to do.
These are here since this module is not complete yet

- Ability to write to screen as well as one or more files
- Per-line setting to decide whether to display or not, and to write or not
- Logging levels (like error, debug, etc)
- This could be done through subclassing
- Needs a way to be fed a dict of {logtype:file} pairs

The default print function was completely remade.
It can safely override the built-in print() function

Timestamps are properly implemented.
This has the ability to split cleverly on long lines.

Next to-do:
- Make the logger() method, to do proper all-around logging
- Implement arbitrary string replacing from within another module (translating)
- Add ability to view docstrings properly (already implemented elsewhere)
"""

from datetime import datetime
import shutil
import time
import sys
import os

class NoValue:
    """Used to express the lack of value as None can be a value."""

    def __repr__(self):
        return 'NoValue'

    def __bool__(self):
        return False

NoValue = NoValue()

class Container:
    """Base container class for various purposes."""

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
        try:
            if self._items == other._items:
                return True
            if set(self._items) == set(other):
                return True
        except:
            return False
        return False

    def __ne__(self, other):
        """Return True if self and other are not identical, False otherwise."""
        return not self.__eq__(other)

_bps = []

for _sub in ("Keys", "Values", "Items", "Types", "Pairs", "Attributes"):
    _bp_doc = """Return all the %s of the class.""" % _sub.lower()
    _bps.append(type("Bypassers" + _sub, (Container,), {'__doc__': _bp_doc}))

class BaseMapping(Container):
    """Lightweight class for inner iteration."""

    def add(self, item):
        """Add a new item to the set."""
        self._items.add(item)

    def remove(self, item):
        """Remove an item from the set."""
        self._items.remove(item)

    def update(self, new):
        """Update the set with new."""
        self._items.update(new)

_mps = []

for _sub in ("Types", "Pairs"):
    _mp_doc = """Subclass for the %s argument.""" % _sub.lower()
    _mps.append(type(_sub + "Mapping", (BaseMapping,), {'__doc__': _mp_doc}))

class InnerMapping(Container):
    """Special mapping used by the Bypassers class for types and pairs."""

    def __init__(self, types=None, pairs=None):
        """Create a new inner iterable."""
        if types is None:
            types = set()
        if pairs is None:
            pairs = set()
        self.types = _mps[0](types)
        self.pairs = _mps[1](pairs)

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
                                        five-tuple or add a new binding

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
            self._items[setting] = [InnerMapping(types, pairs), module, attr]

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

    def __eq__(self, other):
        """Return True if self and other are identical, False otherwise."""
        try:
            return self.items() == other.items()
        except:
            return False

    def __dir__(self):
        """Return a list of all methods of the class."""
        return dir(self.__class__)

    def update(self, new):
        """Update the setting's bindings."""
        setting, types, pairs, module, attr = new
        if setting in self._items:
            self._items[setting][0].types.update(types)
            self._items[setting][0].pairs.update(pairs)
        else:
            self._items[setting] = [InnerMapping(types, pairs), NoValue, NoValue]
        if module is NoValue:
            module = self._items[setting][1]
        if attr is NoValue:
            attr = self._items[setting][2]
        self._items[setting][1:] = [module, attr]

    def extend(self, items):
        """Add a new binding of (setting, types, pairs, module, attr)."""
        setting, types, pairs, module, attr = items
        self._items[setting] = [InnerMapping(types, pairs), module, attr]

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
        """Unbind and return all attributes of a random setting."""
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

    def setdefault(self, item, fallback=NoValue):
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
        return _bps[0](self._items)

    def values(self):
        """Return all values."""
        reader = []
        for (types, pairs), module, attr in self._items.values():
            reader.append((types, pairs, module, attr))
        return _bps[1](reader)

    def items(self):
        """Return all existing five-tuples."""
        reader = []
        for setting, ((types, pairs), module, attr) in self._items.items():
            reader.append((setting, types, pairs, module, attr))
        return _bps[2](reader)

    def types(self):
        """Return all types."""
        reader = []
        for (types, pairs), module, attr in self._items.values():
            reader.append(types)
        return _bps[3](reader)

    def pairs(self):
        """Return all pairs."""
        reader = []
        for (types, pairs), module, attr in self._items.values():
            reader.append(pairs)
        return _bps[4](reader)

    def read(self):
        """Return all (module, attr) tuples."""
        reader = []
        for inner, module, attr in self._items.values():
            reader.append((module, attr))
        return _bps[5](reader)

    def copy(self):
        """Return a new instance with the same attributes."""
        new = []
        for setting, ((types, pairs), module, attr) in self._items.items():
            new.append((setting, types.copy(), pairs.copy(), module, attr))
        return self.__class__(*new)

    def clear(self):
        """Remove all settings and their bindings."""
        self._items.clear()

class BaseLogger:
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

def check_bypass(func):
    """Decorator for checking bypassability for the Logger class."""
    def inner(self, *output, type=None, **rest):
        self.bypassed = {} # reset the bypasses everytime
        for setting, types, pairs, module, attr in self.bypassers.items():
            if type is not None and type in types:
                if module is None:
                    self.bypassed[setting] = attr
                else:
                    self.bypassed[setting] = getattr(module, attr,
                                                     module[attr])
                return func(*output, type=type, **rest)
            for mod, att in pairs:
                if mod is None and att:
                    if module is None:
                        self.bypassed[setting] = attr
                    elif module is not NoValue and attr is not NoValue:
                        self.bypassed[setting] = getattr(module, attr,
                                                         module[attr])
                    else:
                        raise AttributeError("no value assigned to the %s" %
                              "module" if module is NoValue else "attribute")
                    return func(*output, type=type, **rest)
                if getattr(mod, att, mod[att]):
                    if module is None:
                        self.bypassed[setting] = attr
                    elif module is not NoValue and attr is not NoValue:
                        self.bypassed[setting] = getattr(module, attr,
                                                         module[attr])
                    else:
                        raise AttributeError("no value assigned to the %s" %
                              "module" if module is NoValue else "attribute")
                    return func(*output, type=type, **rest)

    return inner

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

        Default:    {"normal": "logger.log", "all": "mixed.log"}

    bypassers:      This is an iterable of (setting, types, pairs, module,
                    attr) iterables. 'types' is an iterable of all types that
                    can match this bypasser. 'pairs' is an iterable of
                    two-tuples, the first argument is the module, a
                    dictionary or None, the second argument is the attribute
                    to search for in the module or dict; if the module is None,
                    the bypassers will use the attribute as its direct value
                    look-up. After this mangling, if the value is True in a
                    boolean context, then the override will occur, and the
                    setting's value will be overridden by the module and
                    attribute's look-up, in the same way that the pairs are
                    check for truth testing. 'setting' is the setting to bypass
                    when the previously-mentioned conditionals evaluate to
                    True, so if at least one of the types matches the type that
                    the logger was called with, or if the value evaluates to
                    True. Do note that the types and pairs parameters expect
                    sets as parameters, and will fail if not given as such.
                    This is done to allow the values to be modified and for the
                    modifications to carry over to the bypassers. This may
                    change in the future for a custom object.

        Default:    () - Converted to a dynamic instance at runtime

    ignore_all:     Set of types to ignore when using the Logger.multiple
                    method. It will not write to the files associated with
                    any type present in this set.

        Default:    set()
    """

    def __init__(self, separator=" ", ending="\n", file=None, use_utc=False,
                 ts_format="[%Y-%m-%d] (%H:%M:%S UTC{tzoffset})", write=True,
                 display=True, logfiles=None, bypassers=(), ignore_all=None):

        BaseLogger.__init__(self, separator, ending, file, use_utc, ts_format)

        self.display = display
        self.write = write

        self.logfiles = {"normal": "logger.log", "all": "mixed.log"}
        if logfiles is not None:
            self.logfiles.update(logfiles)

        # this needs to be list/tuple of (setting, types, pairs, module, attr)
        # tuples; the setting is the setting to bypass; types is a list of
        # types to check for to determine if bypassing should occur, same
        # about the pairs, except for module/attr matches; module and attr are
        # used with getattr() to bypass the value of setting with the one found
        # in the given module, for the given attribute; module of None means
        # to use the attr as the direct value; making the type None will also
        # indicate that any type can be triggered. to indicate a lack of value
        # for any parameter, pass NoValue, as None has a special meaning
        self.bypassers = Bypassers(
                         ("timestamp", set(), set(), NoValue, NoValue),
                         ("splitter", set(), set(), NoValue, NoValue),
                         ("display", set(), set(), NoValue, NoValue),
                         ("logall", set(), set(), NoValue, NoValue),
                         ("write", set(), set(), NoValue, NoValue),
                         ("all", set(), set(), NoValue, NoValue),
                        )

        for bp in bypassers:
            self.bypassers.update(bp)

        self.ignore_all = set()
        if ignore_all is not None:
            self.ignore_all.update(ignore_all)

    @check_bypass
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
        timestamp = self.bypassed.get("timestamp",
                    self._get_timestamp(use_utc, ts_format))
        logall = self.bypassed.get("logall") # file to write everything to
        toget = output.split("\n")
        output = toget.pop(0)

        # check for settings to bypass, if applicable
        if 'splitter' in self.bypassed:
            split = self.bypassed['splitter']
        if 'display' in self.bypassed:
            display = self.bypassed['display']
        if 'write' in self.bypassed:
            write = self.bypassed['write']

        if display:
            self._print(output, file=file, sep=sep, end=end, split=split)
        if write:
            alines = [x for x in self.logfiles if x in
                                 self.bypassers["all"].types]
            getter = [file]
            if logall:
                getter.append(logall)
            for log in getter:
                exists = os.path.isfile(log)
                def atypes(out):
                    if log == logall and type in alines:
                        out = "type.%s - %s" % (type, out)
                    return out
                with open(log, "a", encoding="utf-8") as f:
                    for writer in output.split("\n"):
                        f.write(timestamp + atypes(writer) + "\n")

    def multiple(self, *output, types=None, display=None, write=None, **rest):
        """Log one or more line to multiple files."""
        if types is None:
            types = ["normal"]

        if "*" in types and len(types) == 1:
            for log in self.logfiles:
                if log not in self.ignore_all:
                    self.logger(*output, type=log, display=display,
                                 write=write, **rest)
                    display = False # only display once, if applicable

        elif types:
            for log in types:
                self.logger(*output, type=log, display=display, write=write,
                            **rest)
                display = False

        else:
            self.logger(*output, display=display, write=write, **rest)

    def show(self, *output, type="show", display=True, write=False, **rest):
        """Explicit way to only print to screen."""
        self.logger(*output, type=type, display=display, write=write, **rest)
