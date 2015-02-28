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

class Bypassers:
    """Special mapping used by the bypassers argument of the Logger class.

    This mapping is aimed at emulating a dictionnary, and as such has the same
    methods that a dictionnary has. However, due to the fact this mapping can
    take up to five arguments instead of the standard one or two, more methods
    were added, named after standard methods from other 

    Functional API:

    Notes: This API provides functionality to allow any of the five arguments
    to be read and modified. If you want to use this functional API yourself,
    you must first read this documentation, as some actions do not behave as
    they would be normally expected to due to the unique nature of this mapping.

    bypassers = Bypassers((setting, [types], [(module, attr)], module, attr))

    types = bypassers[setting]          Gets the types bound to this setting

    bypassers[setting] = types          Binds new types to this setting

    bypassers[setting].action           Performs action on the types list

    del bypassers[setting]              Removes the setting and all bindings

    str(bypassers) | repr(bypassers)    Shows all the settings, types, modules
                                        and attributes currently active.

    len(bypassers)                      Returns the amount of bound settings;
                                        to get all settings, use dir()

    x in bypassers                      Returns True if x is a bound setting,
                                        False otherwise

    for x in bypassers                  Iterates over all settings

    bool(bypassers)                     Returns True if at least one setting is
                                        bound, False otherwise

    dir(bypassers)                      Returns a list of all settings

    bypassers.update(setting, iters)    Binds a module and attribute to the
                                        setting. 'iters' must be an iterable of
                                        (module, attr). Types are not altered.

    bypassers.append(setting, iters)    Adds a new (module, attr) pair

    bypassers.remove(setting, iters)    Removes a (module, attr) pair

    bypassers.extend(iterable)          Adds a new binding; expects five-tuple

    bypassers.add(setting)              Adds a new unbound setting

    bypassers.insert(setting, items)    Inserts items into the setting; the
                                        setting must exist. 'items' is an
                                        iterable of (types, values, module,
                                        attr); the types will be appended to
                                        the existing ones, as well as the
                                        values. To add a new entry, use .extend

    bypassers.pop(setting)              Returns the (types, values, module,
                                        attr) iterable bound to setting and
                                        removes all the setting's bindings.

    bypassers.popitem()                 Removes and returns a random pair of
                                        (setting, types, values, module, attr)

    bypassers.get(setting, fallback)    Returns the (types, values, module,
                                        attr) iterable bound to the setting. If
                                        the setting does not exist, 'fallback'
                                        will be returned; defaults to None.

    bypassers.setdefault(item, fb)      Sets the default fallback for setting
                                        'item' to 'fb'; this only affects .get

    bypassers.count(iters)              Returns the number of settings which
                                        are set to use this (module, attr) pair

    bypassers.keys()                    Returns all existing settings

    bypassers.values()                  Returns pairs of (module, attr) tuples

    bypassers.items()                   Returns pairs of keys and values in
                                        (setting, module, attr) tuples

    bypassers.copy()                    Returns a new instance with the same
                                        attributes.

    bypassers.clear()                   Removes all bindings

    Equality testing (== and !=) can be used to compare two different instances
    of the _Bypassers mapping. If they have exactly the same mapping (same
    settings bound to the same types, module and attribute), both instances
    will be considered as equal. This also works even if the other instance is
    not a _Bypassers instance, provided they have an identical API. To check if
    two variables are the same instance, use 'is' instead.

"""

    def __init__(self, *names):
        self.bpdict = {}
        self.fallbacks = {}
        for setting, types, values, module, attr in names:
            self.bpdict[setting] = [list(types), list(values), module, attr]

    def __getitem__(self, item):
        return self.bpdict[item][0]

    def __setitem__(self, item, value):
        self.bpdict[item][0] = list(value) # need to keep a mutable object

    def __delitem__(self, item):
        del self.bpdict[item]

    def __contains__(self, item):
        if item in self.bpdict:
            if self.bpdict[item][0] or self.bpdict[item][1]:
                return True
        return False

    def __len__(self):
        cnt = 0
        for item in self.bpdict:
            if self.bpdict[item][0] or self.bpdict[item][1]:
                cnt += 1
        return cnt

    def __iter__(self):
        return iter(self.bpdict)

    def __eq__(self, other):
        try:
            if set(self.bpdict) == set(other.bpdict):
                for setting, items in self.bpdict.items():
                    if other.bpdict[setting] != items:
                        return False
                return True # either the same instance or identical dicts
        except:
            return False
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        args = []
        for setting in self.bpdict:
            types, values, module, attr = self.bpdict[setting]
            args.append("(setting=%r, types=%r, values=%r, module=%r, attr=%r)"
                       % (setting, types, values, module, attr))
        return '%s(%s)' % (self.__class__.__name__, " | ".join(args))

    def __bool__(self):
        for item in self.bpdict:
            if self.bpdict[item][0] or self.bpdict[item][1]:
                return True
        return False

    def __dir__(self):
        return list(self.bpdict.keys())

    def update(self, setting, bpdict):
        module, attr = bpdict
        if setting not in self.bpdict:
            self.bpdict[setting] = [[], [], NoValue, NoValue]
        if module is not NoValue:
            self.bpdict[setting][2] = module
        if attr is not NoValue:
            self.bpdict[setting][3] = attr

    def append(self, setting, iters):
        if setting not in self.bpdict:
            self.bpdict[setting] = [[], [], NoValue, NoValue]
        self.bpdict[setting][1].append(iters)

    def remove(self, setting, iters):
        self.bpdict[setting][1].remove(iters)

    def extend(self, items):
        setting, types, values, module, attr = items
        self.bpdict[setting] = [list(types), list(values), module, attr]

    def add(self, setting):
        if setting in self.bpdict:
            return
        self.bpdict[setting] = [[], [], NoValue, NoValue]

    def insert(self, setting, new):
        types, values, module, attr = new
        oldt = self.bpdict[setting][0]
        oldv = self.bpdict[setting][1]
        oldt.extend(types)
        oldv.extend(values)
        self.bpdict[setting][0] = oldt
        self.bpdict[setting][1] = oldv
        if module is not NoValue:
            self.bpdict[setting][2] = module
        if attr is not NoValue:
            self.bpdict[setting][3] = attr

    def pop(self, item):
        return self.bpdict.pop(item)

    def popitem(self):
        setting, (types, values, module, attr) = self.bpdict.popitem()
        return (setting, types, values, module, attr)

    def get(self, item, fallback=NoValue):
        if item not in self.bpdict:
            if item in self.fallbacks and fallback is NoValue:
                fallback = self.fallbacks[item]
            return fallback
        return tuple(self.bpdict[item])

    def setdefault(self, item, fallback=None):
        self.fallbacks[item] = fallback
        if fallback is NoValue:
            del self.fallbacks[item]

    def count(self, iters):
        cnt = 0
        module, attr = iters
        for mod, att in self.values():
            if mod == module and att == attr:
                cnt += 1
        return cnt

    def keys(self):
        return list(self.bpdict.keys())

    def values(self):
        val = []
        for item in self.bpdict.values():
            val.append((item[2], item[3]))
        return val

    def items(self):
        module = []
        attr = []
        for m, a in self.values():
            module.append(m)
            attr.append(a)
        return list(zip(self.keys(), module, attr))

    def copy(self):
        new = []
        for setting, (types, values, module, attr) in self.bpdict.items():
            new.append((setting, types, values, module, attr))
        return self.__class__(*new)

    def clear(self):
        self.bpdict.clear()

class LoggerMeta(type):
    """Metaclass for the Logger classes.

    The base class' docstring carries over to all subclasses."""

    def __new__(metacls, cls, bases, classdict):
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
                    newdoc = somecls.__doc__ + "\n\n" + " -" * (col // 2 - 1)
                    if newcls.__doc__:
                        newcls.__doc__ = newdoc + "-\n\n" + newcls.__doc__
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
        """Returns a timestamp with timezone + offset from UTC."""
        if use_utc is None:
            use_utc = self.use_utc
        if ts_format is None:
            ts = self.ts_format
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
        """Safe way to print to screen or to a file.

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
        """Sanitizes output and joins iterables together."""
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

    ignorers:       Dictionary of {setting:[types]} pairs. This can be used
                    when instantiating the class to allow more customization
                    over various calls, to ignore certains settings for
                    certtain types. This will internally set the setting to
                    False if and when applicable. See 'bypassers' if you wish
                    to use any arbitrary value.

        Default:    {"timestamp": [], "all": [], "split": []}

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
                 display=True, logfiles={}, ignorers={}, bypassers=()):

        BaseLogger.__init__(self, separator, ending, file, use_utc, ts_format)

        self.display = display
        self.write = write

        self.logfiles = {"normal": "logger.log"}
        self.logfiles.update(logfiles)

        self.ignorers = {"timestamp": [], "all": [], "splitter": []}
        self.ignorers.update(ignorers)

        # this needs to be list/tuple of (setting, type, module, attr) tuples;
        # the setting is the setting to bypass; type is the type to check for
        # to determine if bypassing should occur; module and attr are used
        # with getattr() to bypass the value of setting with the one found
        # in the given module, for the given attribute; module of None means
        # to use the attr as the direct value; making the type None will also
        # indicate that any type can be triggered. to indicate a lack of value
        # for any parameter, pass NoValue as None has a special meaning
        self.bypassers = Bypassers(*bypassers)

    def logger(self, *output, file=None, type=None, display=None, write=None,
               sep=None, end=None, split=True, use_utc=None, ts_format=None):
        """Logs everything to screen and/or file. Always use this."""
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
