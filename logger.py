﻿# Copyright (c) 2015, Emanuel Barry
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Improved Logger module by Vgr v0.1
Documentation string still to-do.
This module is complete, but bugs might be lying around.
Next up is writing this docstring, then a lot of testing."""

__all__ = ["Bypassers", "BaseLogger", "Logger", "Translater", "NoValue"]

from datetime import datetime
import random
import shutil
import time
import sys
import re

class NoValue:
    """Used to express the lack of value, as None has a special meaning."""

    def __repr__(self):
        """Return the explicit NoValue string."""
        return 'NoValue'

    def __bool__(self):
        """Return False no matter what."""
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

    def __dir__(self):
        """Return a list of all methods."""
        return dir(self.__class__) + list(x for x in self.__dict__
                                   if x[0] != "_" or x[:2] == x[-2:] == "__")

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

    def __lt__(self, other):
        """Return True if self is less than other, False otherwise."""
        return sorted(self._items) < sorted(other)

    def __le__(self, other):
        """Return True if self is less or equal to other, False otherwise."""
        return sorted(self._items) <= sorted(other)

    def __gt__(self, other):
        """Return True if self is greater than other, False otherwise."""
        return sorted(self._items) > sorted(other)

    def __ge__(self, other):
        """Return True if self is greater or equal to other, False otherwise."""
        return sorted(self._items) >= sorted(other)

    def __getattr__(self, attr):
        """Delegate an attribute not found to the items set."""
        return getattr(self._items, attr)

_mps = []

for _sub in ("Types", "Pairs"):
    _mp_doc = """Subclass for the %s argument.""" % _sub.lower()
    _mps.append(type(_sub + "Mapping", (BaseMapping,), {'__doc__': _mp_doc}))

class Viewer(Container):
    """Viewer object for the Bypassers mapping."""

    def __init__(self, __self__):
        """Create a new viewer handler."""
        self.__self__ = __self__
        self._items = __self__._items

    def __repr__(self):
        """Return a representation of self."""
        return "%s(%s)" % (self.__self__.__class__.__name__,
               ", ".join(repr(item) for item in sorted(self._items)))

class BaseViewer:
    """Base viewer class for the Bypassers mapping."""

    def __init__(self, __self__):
        """Create a new view object."""
        self.__self__ = __self__
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
        return dir(self.__class__) + ["__self__"]

    def __repr__(self):
        """Return a representation of the viewer."""
        return "<%s view object of the %s object at %s>" % (
               self.__class__.__name__,
               self.__self__.__class__.__name__,
               "0x" + hex(id(self.__self__))[2:].zfill(16).upper())

    def __call__(self):
        """Return the view object."""
        return self._viewer

    def __getattr__(self, attr):
        """Delegate any attribute not found to the inner list."""
        return getattr(self._items, attr)

def make_sub(name):
    """Generate view objects."""
    subs = []
    for sub in ("Keys", "Types", "Pairs", "Attributes", "Values", "Items"):
        doc = """Return all the %s of the %s class.""" % (sub.lower(), name)
        subs.append(type(name + sub, (BaseViewer,), {'__doc__': doc}))
    return subs

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

    bypassers = Bypassers((setting, {types}, {(module, attr)}, module, attr))

    bypassers[setting]                  Access the internal mapping of types
                                        and pairs

    del bypassers[setting]              Remove the setting and all bindings

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

    bypassers.add(setting)              Add new unbound settings

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

    bypassers.copy()                    Return a deep copy of the mapping

    bypassers.clear()                   Remove all settings and their bindings

    Equality testing (== and !=) can be used to compare two different instances
    of the Bypassers mapping. If they have exactly the same mapping (same
    settings bound to the same types, pairs, module and attribute), both
    instances will be considered to be equal. This also works even if the other
    instance is not a Bypassers instance, provided they have an identical API.
    To check if two variables are the same instance, use 'is' instead.

    The view objects of this class are changeable. This means that they reflect
    any changes that happened to the mapping. It is also guaranteed that the
    view objects' items will be sorted in alphabetical order.
    """

    def __init__(self, *names):
        """Create a new instance of the class."""
        self._fallbacks = {}
        self._names = ("keys", "types", "pairs", "read", "values", "items")
        self._mappers = make_sub(self.__class__.__name__)
        for i, name in enumerate(self._names):
            setattr(self, name, self._mappers[i](self))
        for name in names:
            new = (name,)
            if hasattr(name, "items"):
                new = name.items()
            for setting, types, pairs, module, attr in new:
                types = _mps[0](types)
                pairs = _mps[1](pairs)
                self.keys.append(setting)
                self.types.append(types)
                self.pairs.append(pairs)
                self.read.append((module, attr))
                self.values.append((types, pairs, module, attr))
                self.items.append((setting, types, pairs, module, attr))

    def __getitem__(self, item):
        """Return the internal mapping of the setting."""
        return self.values[self.keys.index(item)]

    def __delitem__(self, item):
        """Remove the setting and all its bindings."""
        index_ = self.keys.index(item)
        for name in self._names:
            del getattr(self, name)[index_]

    def __iter__(self):
        """Return an iterator over the items of self."""
        return iter(self.keys())

    def __len__(self):
        """Return the total number of items, bound or otherwise."""
        return len(self.keys())

    def __contains__(self, item):
        """Return True if item is a setting, False otherwise."""
        return item in self.keys()

    def __bool__(self):
        """Return True if at least one setting is bound, False otherwise."""
        for mapping in (self.types, self.pairs):
            for inner in mapping:
                if inner:
                    return True
        return False

    def __repr__(self):
        """Return a string of all active attributes."""
        args = []
        for setting, types, pairs, module, attr in self.items():
            args.append("(setting=%r, types=%r, pairs=%r, module=%r, attr=%r)"
                       % (setting, types, pairs, module, attr))
        return '%s(%s)' % (self.__class__.__name__, " | ".join(args))

    def __eq__(self, other):
        """Return True if self and other are identical, False otherwise."""
        try:
            return self.items() == other.items()
        except:
            return False

    def update(self, *new):
        """Update the setting's bindings."""
        for name in new:
            item = (name,)
            if hasattr(name, "items"):
                item = name.items()
            for setting, types, pairs, module, attr in item:
                if setting in self.keys():
                    index_ = self.keys.index(setting)
                    self.types[index_].update(types)
                    self.pairs[index_].update(pairs)
                else:
                    index_ = len(self.keys())
                    types = _mps[0](types)
                    pairs = _mps[1](pairs)
                    self.keys.append(setting)
                    self.types.append(types)
                    self.pairs.append(pairs)
                    self.read.append((NoValue, NoValue))
                    self.values.append((types, pairs, NoValue, NoValue))
                    self.items.append((setting, types, pairs, NoValue, NoValue))
                if module is NoValue:
                    module = self.read[index_][0]
                if attr is NoValue:
                    attr = self.read[index_][1]
                self.read[index_] = (module, attr)
                self.values[index_] = self.values[index_][:2] + (module, attr)
                self.items[index_] = self.items[index_][:3] + (module, attr)

    def extend(self, items):
        """Add a new binding of (setting, types, pairs, module, attr)."""
        setting, types, pairs, module, attr = items
        if setting in self.keys():
            index_ = self.keys.index(setting)
            self.types[index_].update(types)
            self.pairs[index_].update(pairs)
            if module is NoValue:
                module = self.read[index_][0]
            if attr is NoValue:
                attr = self.read[index_][1]
            self.read[index_] = (module, attr)
            self.values[index_] = self.values[index_][:2] + (module, attr)
            self.items[index_] = self.items[index_][:3] + (module, attr)
        else:
            types = _mps[0](types)
            pairs = _mps[1](pairs)
            self.keys.append(setting)
            self.types.append(types)
            self.pairs.append(pairs)
            self.read.append((module, attr))
            self.values.append((types, pairs, module, attr))
            self.items.append((setting, types, pairs, module, attr))

    def add(self, *settings):
        """Add new unbound settings. Ignored for existing settings."""
        for setting in settings:
            if setting in self.keys():
                continue
            types = _mps[0](set())
            pairs = _mps[1](set())
            self.keys.append(setting)
            self.types.append(types)
            self.pairs.append(pairs)
            self.read.append((NoValue, NoValue))
            self.values.append((types, pairs, NoValue, NoValue))
            self.items.append((setting, types, pairs, NoValue, NoValue))

    def pop(self, item):
        """Remove and return the bindings of setting."""
        index_ = self.keys.index(item)
        types, pairs, module, attr = self.values[index_]
        for name in self._names:
            del getattr(self, name)[index_]
        return (types, pairs, module, attr)

    def popitem(self):
        """Unbind and return all attributes of a random setting."""
        index_ = random.randrange(len(self.keys()))
        setting, types, pairs, module, attr = self.items[index_]
        for name in self._names:
            del getattr(self, name)[index_]
        return (setting, types, pairs, module, attr)

    def get(self, item, fallback=NoValue):
        """Return the settings' bindings, or fallback if not available."""
        if item not in self.keys():
            if item in self._fallbacks and fallback is NoValue:
                fallback = self._fallbacks[item]
            return None if fallback is NoValue else fallback
        types, pairs, module, attr = self.values[self.keys.index(item)]
        return (types, pairs, module, attr)

    def setdefault(self, item, fallback=NoValue):
        """Set the default fallback for the get() method."""
        self._fallbacks[item] = fallback
        if fallback is NoValue:
            del self._fallbacks[item]

    def count(self, iters):
        """Return the amount of (module, attr) bindings in all settings."""
        cnt = 0
        module, attr = iters
        for mod, att in self.read():
            if mod == module and att == attr:
                cnt += 1
        return cnt

    def copy(self):
        """Return a new instance with the same attributes."""
        new = []
        for setting, types, pairs, module, attr in self.items():
            new.append((setting, types.copy(), pairs.copy(), module, attr))
        return self.__class__(*new)

    def clear(self):
        """Remove all settings and their bindings."""
        for name in self._names:
            getattr(self, name).clear()

class BaseLogger:
    """Base Logger class for your everyday needs.

    This can be inherited to create custom classes.
    This is not user-faced. For general purposes, please use the Logger class.
    All arguments have a default value of None, and their stated default value
    is assigned after the call. This can be used to pass None for a parameter
    to ensure it always uses the correct default value, should it change.
    Subclasses defined in this module follow this rule, and any other class
    subclassing it should follow it too. It is also recommended that any method
    defined under such classes follow this rule, although it is not enforced.

    sep:            String to be used to join the lines together.

        Default:    " "

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

    def __init__(self, sep=None, use_utc=None, ts_format=None):
        """Create a new base instance."""

        self.separator = " " if sep is None else sep

        self.use_utc = use_utc or False

        # this can have {tzname} and {tzoffset} for formatting
        # this adds respectively a timezone in the format UTC or EST
        # and an offset from UTC in the form +0000 or -0500
        self.ts_format = ts_format or "[%Y-%m-%d] (%H:%M:%S UTC{tzoffset})"

    def __dir__(self):
        """Return a list of all non-private methods and attributes."""
        items = dir(self.__class__) + list(self.__dict__)
        for item in items[:]:
            if item[0] == "_" and not item[:2] == item[-2:] == "__":
                items.remove(item)
        return items

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

    def _split_lines(self, out, sep):
        """Split long lines at clever points to avoid weird clipping."""
        col = shutil.get_terminal_size()[0]
        if not isinstance(out, str):
            out = sep.join(out) # make any iterable work
        out = out.strip(" ")
        lines = out.splitlines()
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

    def _print(self, *output, sep=None, split=True):
        """Print to screen and remove all invalid characters."""

        sep = self.separator if sep is None else sep

        if split:
            output = self._split_lines(output, sep)

        file = open(sys.stdout.fileno(), "w", errors="replace",
                    encoding="utf-8", closefd=False)

        file.write(sep.join(output) + "\n") # mimic built-in print() behaviour

        file.flush()
        file.close()

        return sep.join(output)

    def _get_output(self, out, sep):
        """Sanitize output and join iterables together."""
        out = out or [''] # called with no argument, let's support it anyway
        msg = None
        for line in out:
            if not isinstance(line, str):
                line = sep.join(line)
            if msg is None:
                msg = line
            else:
                if line == "":
                    line = "\n"
                msg = msg + sep + str(line)
        return msg

def check_bypass(func):
    """Decorator for checking bypassability for the Logger class."""
    def inner(self, *output, type=None, file=None, **rest):
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
        self.bypassed = {} # reset the bypasses everytime
        for setting, types, pairs, module, attr in self.bypassers.items():
            if module is NoValue or attr is NoValue:
                continue
            for mod, att in pairs:
                if mod is None and att:
                    if module is None:
                        self.bypassed[setting] = attr
                    else:
                        self.bypassed[setting] = getattr(module, attr,
                                                         module.get(attr))
                    break

                elif getattr(mod, att, mod.get(att)):
                    if module is None:
                        self.bypassed[setting] = attr
                    else:
                        self.bypassed[setting] = getattr(module, attr,
                                                         module.get(attr))
                    break

            else:
                if type in types and module is None:
                    self.bypassed[setting] = attr
                elif type in types:
                    self.bypassed[setting] = getattr(module, attr,
                                                     module.get(attr))

        return func(self, *output, type=type, file=file, **rest)

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
                    change in the future for a custom object. Do note that
                    this parameter expects an iterable of five-tuples, or
                    an empty iterable.

        Default:    See below (converted to a dynamic instance at runtime)

    Available settings for the bypassers:

    These are the available settings to bypass. Do note that the default of
    all these settings is to not do anything, and must be explicitely set
    otherwise.

    "timestamp":    Will be used to replace the standard timestamp when
                    writing to file. It will not use that value to perform
                    the timestamp getting operation. Rather, it will use the
                    string given directly. If a different timestamp for certain
                    conditions is the desired result, a manual call to the
                    _get_timestamp method will need to be done. This is
                    typically used to remove a timestamp, so it will be used
                    with the pair of (None, ''), effectively removing the
                    timestamp.

    "splitter":     This will be used to determine if clever splitting should
                    occur when printing to screen. Clever splitting splits the
                    line at the latest space before the line gets to the end of
                    the terminal's length. By default, this is True, and can be
                    changed on a per-line basis. This bypasser overrides that.

    "display":      This is used to override the per-line setting that decides
                    whether the line should be printed to the screen. This is
                    set to True by default, and can be overriden on a per-line
                    basis. This bypasser can be used to bypass this setting.

    "write":        This is used to override the per-line setting that decides
                    whether the line should be written to the file or not. This
                    is set to True by default, and can be overriden on a per-
                    line basis. This bypasser can override that parameter.

    "logall":       Defaulting to None, this setting's bypassed value must be
                    a string object, which, if the bypassing occurs, will be
                    used as a file to write everything to.

    The following parameters are not actual bypassers. Only the types bound to
    the setting are of relevance. The pairs are ignored, and so are the
    module and attribute.

    "files":        The types bound to this setting will be used to determine
                    when to write and not to write to certain files. This is
                    only used when using the Logger.multiple method, which will
                    write to all files except those bound to the types in this
                    bypasser.

    "all":          The types bound to this setting will not be written as when
                    writing to the file defined through the 'logall' bypasser,
                    if available.
    """

    def __init__(self, sep=None, use_utc=None, ts_format=None,
                 write=None, display=None, logfiles=None, bypassers=None):
        """Create a new Logger instance."""

        super().__init__(sep, use_utc, ts_format)

        self.display = True if display is None else display
        self.write = True if write is None else write

        files = {"normal": "logger.log", "all": "mixed.log"}

        if logfiles is not None:
            self.logfiles = logfiles
            for type, file in files.items():
                # if the type is already defined, don't overwrite it
                # only add to it if it doesn't exist
                self.logfiles[type] = self.logfiles.get(type, file)
        else:
            self.logfiles = files

        # this needs to be list/tuple of (setting, types, pairs, module, attr)
        # tuples; the setting is the setting to bypass; types is a list of
        # types to check for to determine if bypassing should occur, same
        # about the pairs, except for module/attr matches; module and attr are
        # used with getattr() to bypass the value of setting with the one found
        # in the given module, for the given attribute; module of None means
        # to use the attr as the direct value; making the type None will also
        # indicate that any type can be triggered. to indicate a lack of value
        # for any parameter, pass NoValue, as None has a special meaning
        if bypassers is None:
            bypassers = ()

        self.bypassers = Bypassers(*bypassers)

        self.bypassers.add("timestamp", "splitter", "display", "write",
                           "logall", "files", "all")

    @check_bypass
    def logger(self, *output, file=None, type=None, display=None, write=None,
               sep=None, split=None, use_utc=None, ts_format=None):
        """Log everything to screen and/or file. Always use this."""

        sep = self.separator if sep is None else sep
        split = True if split is None else split
        display = self.display if display is None else display
        write = self.write if write is None else write

        output = self._get_output(output, sep, end)
        timestamp = self.bypassed.get("timestamp",
                    self._get_timestamp(use_utc, ts_format))
        logall = self.bypassed.get("logall") # file to write everything to
        output = output.splitlines()

        # check for settings to bypass, if applicable
        split = self.bypassed.get("splitter", split)
        display = self.bypassed.get("display", display)
        write = self.bypassed.get("write", write)

        if write:
            alines = [x for x in self.logfiles if x in
                                 self.bypassers["all"][0]]
            getter = [file]
            if logall:
                getter.append(logall)
            for log in getter:
                if log == logall and type not in alines:
                    continue
                atypes = "type.%s - " % type if log == logall else ""
                with open(log, "a", encoding="utf-8") as f:
                    for writer in output:
                        f.write(timestamp + atypes + writer + "\n")

        if display:
            return self._print(*output, sep=sep, end=end,
                                split=split).splitlines()
        return output

    def multiple(self, *output, types=None, display=None, write=None, **rest):
        """Log one or more line to multiple files."""
        if types is None:
            types = ["normal"]

        if "*" in types and len(types) == 1:
            for log in self.logfiles:
                if log not in self.bypassers["files"][0]:
                    if display:
                        line = self.logger(*output, type=log, display=True,
                                            write=write, **rest)
                        display = False # only display once, if applicable
                    else:
                        self.logger(*output, type=log, display=False,
                                     write=write, **rest)

            return line

        if types:
            for log in types:
                if display:
                    line = self.logger(*output, type=log, display=True,
                                 write=write, **rest)
                    display = False
                else:
                    self.logger(*output, type=log, display=False, write=write,
                                **rest)

            return line

        return self.logger(*output, display=display, write=write, **rest)

    def show(self, *output, type="show", display=True, write=False, **rest):
        """Explicit way to only print to screen."""
        return self.logger(*output, type=type, display=display, write=write,
                           **rest)

    def docstring(self, *output, tabs=4, display=True, write=False, sep=None,
                        **rest):
        """Print a docstring using proper formatting."""
        newlined = False
        indent = None
        lines = []

        sep = "\n" if sep is None else sep

        output = self._get_output(output, sep)
        for line in output.expandtabs(tabs).splitlines():
            if not newlined and not line.lstrip(): # first empty line
                newlined = True
            elif newlined and indent is None and line.lstrip():
                indent = len(line) - len(line.lstrip())
                line = line.lstrip()
            elif indent is not None:
                if line and line[indent:] == line.lstrip():
                    line = line.lstrip()
                elif (len(line) - len(line.lstrip())) > indent:
                    line = line[indent:]
                elif (len(line) - len(line.lstrip())) < indent:
                    line = line.lstrip()
            lines.append(line)

        while lines and not lines[-1].strip():
            lines.pop()
        while lines and not lines[0].strip():
            lines.pop(0)

        return self.logger(*lines, display=display, write=write, sep=sep
                           **rest)

class Translater(Logger):
    """Logging class to use to translate lines.

    This is inherited from the Logger class.
    The parameters are the same as for the Logger class, with these additions:

    all_languages:  Dictionary of {language:short} pairs. The language is used
                    for the standard lookup of the language. The value is the
                    2-characters abbreviation of the language. The default
                    value is of "English" for the key, and "en" for the value.
                    This must contain all languages that this class will be
                    asked to translate, see below for restrictions.

        Default:    {"English": "en"}

    main:           The main language that will be used. This is considered
                    the "default" language, and is the one that will be used
                    to write to the normal files. It will always be written to
                    the files, no matter what language is being used.

        Default:    "English"

    current:        The current language, used for translating and printing to
                    screen. When writing to one or more files, the files that
                    this language's lines are written into will be prepended
                    with the two-characters short language abbreviation that
                    was given in the all_languages dict, following by a single
                    underscore, and the file's name. This will not be done if
                    the language is the same as the main.

        Default:    "English"

    module:         The module or dictionary where the translations will be
                    looked up. This can be any arbitrary object, as long as
                    either the object has an attribute corresponding to the
                    line to translate (see below for information on how those
                    are looked up), or it implements indexing via module[attr]
                    and 'attr' is in object 'module'. If both are true, only
                    the first will be used. If neither are true, it will print
                    the string as-is. It will never error. It WILL error,
                    however, if the language used is not in 'all_languages'.
                    If it is None, then the 'modules' argument will be
                    checked instead, see below. It will also be checked if the
                    module defined here fails to find the appropriate line.

        Default:    None

    modules:        If the above parameter is set to None or otherwise fails,
                    it will use this parameter instead. It is a mapping of
                    {language:module} pairs that will be used to search for
                    each language. The keys must be in the all_languages
                    mapping as well. The value must be a module (or any object)
                    where the attributes or items are equivalent to the strings
                    that will be passed in. If both the above and this
                    parameter are None, no translating will occur.

        Default:    None

    first:          Determines which, of the line or the language, must be
                    checked first when looking up the translations. The only
                    valid arguments are "line" and "language". Using 'line',
                    the translater will look into the module or mapping for
                    an attribute or item named 'line', and then will look for
                    an attribute or item named like the current language, and
                    will return the matching result. Otherwise, it will look
                    for an item named like the current language, and then for
                    an item named 'line' in it. If 'module' is not defined or
                    fails but 'modules' is, this parameter will be ignored and
                    a single value lookup will be performed.

                    Note about custom objects: The lookup uses getattr()
                    followed by item.get() if the former fails, falling back
                    to printing the line as-is if it fails.

        Default:    "language"

    pattern:        Regex pattern that determines when a line should be given
                    to the translater for replacing. If a line doesn't match,
                    it will not be translated.

        Default:    "[A-Z_]*" - UPPERCASE_UNDERSCORED_NAMES

    Note on ignoring translation for certain lines: To prevent certain lines
    from being translated, use the "translate" setting for the bypassers,
    passing a five-tuple with the first item being "translate". The second item
    is an iterable (a set is the supported type) of types that should not be
    translated. The third item is another iterable (again, the Bypassers were
    made to support a set), consisting of (module, attr) pairs, where the
    module can be any object or None, and the attribute can be an attribute or
    item of the module or, if the module is None, the direct value will be
    looked up instead. The last two parameters can be anything (but must be
    present), they will be replaced at runtime. They are only used internally
    to determine when not to translate.

    Note on translating: The translated lines can take new-style formatting
    with {0} or similar; it can use list indexes, regular indexes or named
    indexes like {foo}. Assign an ordered iterable for the numeric indexes
    with the 'format' argument of the logger method, and a mapping to the
    'format_dict' argument of the logger method. Old-style formatting using
    the modulus (%) operand may still be used, by passing a sequence or mapping
    to the 'format_mod' argument of the logger method. It is up to the user to
    make sure that the proper type of iterable is given, with the proper
    arguments in the string. Numerical and named arguments cannot be mixed for
    old-style formatting. The new-style formatting is the recommended method.
    Unlike new-style formatting, the modulus method can fail if the incorrect
    amount of parameters are given. Both formatting methods can be used at the
    same time. Also, do note that it IS possible to give strings matching the
    regex pattern to format, and they will be properly translated as well. It
    is not, however, possible to loop through these recursively. The formatting
    rules would become too complicated for the small benefit that such a
    feature would provide. If one really needs to do so, they can call the
    logger method recursively on their own.

    Worth of note: The modulus-style formatting is applied after the new-style
    formatting. This makes it easier to go one layer deeper into the
    formatting, and allow for formatting from inside the previsouly-formatted
    lines.

    If translating directly without using the logger method, here are a few
    useful bits of information:

    - It operates through side-effect. This means that it doesn't return any
      value, rather, it directly alters the list given. If the object passed
      in as the first parameter is not mutable, an exception will occur. This
      restriction does not apply to the formats.

    - It takes five arguments (besides self). The first argument is the mutable
      object used for the output (and which will be altered). The second
      argument is the language. This will be used for looking up which line
      lines to use. The 3 other arguments are used for formatting, post-
      translation. All 3 arguments must be given. The first of the three
      is to be used as the numerical formatting using new-style string
      formatting (the str.format method). The second is a mapping to be used
      in the new-style formatting as well. The third one can be either a
      (mutable) sequence or mapping, and is used for old-style formatting
      (modulus formatting with the % operand). It will be applied after the
      new-style formatting has been applied.

    - It makes sure to retain the original class of the formats iterables
      passed in, if it can. The class of each variable needs to define a copy
      method, if it does, it will be used. If there are no copy methods, it
      will use the default expectation of what the iterable should be; a list
      for 'format' and 'format_mod', and a dict for 'format_dict'; this is done
      to accept any object, not just built-in ones.
"""

    def __init__(self, sep=None, use_utc=None, ts_format=None, display=None,
                 write=None, logfiles=None, bypassers=None, all_languages=None,
                 main=None, current=None, module=None, modules=None,
                 first=None, pattern=None):
        """Create a new translater object."""

        super().__init__(sep, use_utc, ts_format, display, write,
                         logfiles, bypassers, ignore_all)

        langs = {"English": "en"}

        if all_languages is not None:
            self.all_languages = all_languages
            for long, short in langs.items():
                self.all_languages[long] = self.all_languages.get(long, short)
        else:
            self.all_languages = langs

        self.main = main or "English"
        self.current = current or "English"

        self.bypassers.update(("translate", set(), set(), None, True))

        self.module = module
        self.modules = modules

        self.first = first or "language"
        self.pattern = pattern or "[A-Z_]*"

    def translate(self, output, language, format, format_dict, format_mod):
        """Translate a line into the desired language."""

        format = getattr(format.__class__, "copy", list)(format)
        format_dict = getattr(format_dict.__class__, "copy", dict)(format_dict)
        format_mod = getattr(format_mod.__class__, "copy", list)(format_mod)

        def enum(iterable):
            if hasattr(iterable, "items"):
                return iterable.items()
            return enumerate(iterable)

        # for loops are amazing and incredible
        for iterable in (format, format_dict, format_mod, output):
            for i, line in enum(iterable):
                if re.fullmatch(self.pattern, line):
                    original = line
                    module = line
                    lang = None
                    if self.module is not None:
                        if first == "line":
                            module = getattr(self.module, line,
                                                  module.get(line, line))
                        else:
                            module = getattr(self.module, language,
                                                  module.get(language, line))

                    if module == line and self.modules is not None:
                        lang = self.modules.get(language)
                        if lang is not None:
                            module = getattr(lang, line, lang.get(line, line))

                    if module != line:
                        if lang is None:
                            if first == "line":
                                line = getattr(module, language,
                                               module.get(language, line))
                            else:
                                line = getattr(module, line,
                                               module.get(line, line))

                        else:
                            line = module

                    if line != original and iterable == output:
                        line = line.format(*format, **format_dict) % format_mod

                    iterable[i] = line

    @check_bypass
    def logger(self, *output, file=None, type=None, display=None, write=None,
               sep=None, split=None, use_utc=None, ts_format=None,
               language=None, format=None, format_dict=None, format_mod=None):
        """Log a line after translating it."""

        sep = self.separator if sep is None else sep

        language = language or self.current

        format = format or ()
        format_dict = format_dict or {}
        format_mod = format_mod or ()

        output = self._get_output(output, sep).split(sep)

        if self.bypassed.get("translate") is None and language != self.main:
            trout = output[:]
            self.translate(trout, language, format, format_dict, format_mod)

            trfile = self.all_languages[language] + "_" + file

            super().logger(*trout, file=trfile, type=type, display=display,
                            write=write, sep=sep, split=split,
                            use_utc=use_utc, ts_format=ts_format)

            display = False

        self.translate(output, self.main, format, format_dict, format_mod)

        return super().logger(*output, file=file, display=display, write=write,
                               sep=sep, split=split, use_utc=use_utc,
                               ts_format=ts_format)
