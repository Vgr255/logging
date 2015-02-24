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
- Add a write() method to write to files properly
- Make the logger() method, to do proper all-around logging
- Implement a way to bypass some settings
- Implement arbitrary string replacing from within another module (translating)
- Add ability to view docstrings properly (already implemented elsewhere)
"""

from datetime import datetime
import shutil
import time
import sys

def _is_file_or_desc(obj):
    """Returns True if obj is a file or file descriptor, False otherwise."""
    # we don't care what the obj is, if it has 'write' it's up to them
    # to implement it properly; str, int or byteswill have open() used on them
    return hasattr(obj, "write") or isinstance(obj, (str, int, bytes))

def _is_valid_encoder(enc):
    """Returns True if enc is a valid encoding, False otherwise."""
    try:
        b' '.decode(enc)
        return True
    except LookupError:
        return False

def _get_type(obj): # hacky way around types
    """Returns the type of obj."""
    return repr(type(obj))[8:-2]

class BaseLogger:
    """Base Logger class for your everyday needs.

    This can be inherited to create custom classes.
    This is not user-faced. For general purposes, please use the Logger class.

    Usage: BaseLogger(
           encoding = "utf-8",
           separator = " ",
           ending = "\n",
           file = None,
           use_utc = False,
           ts_format = "[%Y-%m-%d] (%H:%M:%S UTC{tzoffset})",
           )

    encoding:       Defines the encoding method to use for decoding bytes
                    object. Will raise a TypeError if not a valid encoding.

        Default:    "utf-8"

    separator:      String or bytes object to join the lines together.
                    If the separator or any line is a bytes object, all str
                    objects will be converted to bytes.

        Default:    " "

    ending:         String or bytes object to append at the end of the lines.
                    This can be a str or bytes object. Again, if it is a bytes
                    object, the resulting line will be converted to one.

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

    def __init__(self, encoding="utf-8", separator=" ", ending="\n",
                 file=None, use_utc=False,
                 ts_format="[%Y-%m-%d] (%H:%M:%S UTC{tzoffset})"):

        self.encoding = encoding
        self.separator = separator
        self.ending = ending

        self.file = file
        self.fb_file = sys.stdout

        self.use_utc = use_utc

        # this can have {tzname} and {tzoffset} for formatting
        # this adds respectively a timezone in the format UTC or EST
        # and an offset from UTC in the form +0000 or -0500
        self.ts_format = ts_format

        if not _is_valid_encoder(self.encoding):
            raise TypeError("%r is not a valid encoding" % self.encoding)

        # all those type checkings are done to ensure we catch any error as
        # soon as possible, instead of having something blow up down the road;
        # the functions will expect a string and will fail if not given as such
        if not isinstance(self.separator, (str, bytes)):
            raise TypeError("expected str or bytes, got %r"
                            % _get_type(self.separator))

        if not isinstance(self.ending, (str, bytes)):
            raise TypeError("expected str or bytes, got %r"
                            % _get_type(self.ending))

    def _get_timestamp(self, use_utc=None, ts_format=None):
        """Returns a timestamp with timezone + offset from UTC."""
        if use_utc is None:
            use_utc = self.use_utc
        if ts_format is None:
            ts = self.ts_format
        if use_utc:
            tmf = datetime.utcnow().strftime(timestamp_format)
            tz = "UTC"
            offset = "+0000"
        else:
            tmf = time.strftime(timestamp_format)
            tz = time.tzname[0]
            offset = "+"
            if datetime.utcnow().hour > datetime.now().hour:
                offset = "-"
            offset += str(time.timezone // 36).zfill(4)
        return tmf.format(tzname=tz, tzoffset=offset).strip().upper() + " "

    def _split_lines(self, out, enc="utf-8", sep=" ", end="\n"):
        """Split long lines at clever points to avoid weird clipping."""
        col = shutil.get_terminal_size()[0]
        _sp = (" ", "\n", "")
        if any((isinstance(sep, bytes), isinstance(end, bytes),
              (not isinstance(out, (str, bytes)) and any(isinstance(x, bytes)
              for x in out)), isinstance(out, bytes))):

            _sp = (b" ", b"\n", b"")
            if not isinstance(out, (str, bytes)):
                out = [x.encode(enc) if isinstance(x, str) else x for x in out]
            elif isinstance(out, str):
                out = out.encode(enc)

        if not isinstance(out, (str, bytes)):
            out = sep.join(out) # make any iterable work
        out = out.strip(_sp[0])
        lines = out.split(_sp[1])
        splines = [line.split() for line in lines]
        newlines = [] # newline-separated lines
        for i, line in enumerate(lines):
            if len(line) <= col:
                newlines.append(line)
                continue
            newstr = _sp[2]
            for word in splines[i]:
                if newstr:
                    new = _sp[0].join((newstr, word))
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

    def _make_all_equal(self, *stuff, encoding=None):
        """Convert str objects to bytes if there's at least a bytes object."""
        if encoding is None:
            encoding = self.encoding
        for s in stuff:
            if isinstance(s, bytes) or any(isinstance(x, bytes) for x in s):
                break
        else: # no bytes object
            return stuff
        _all = list(stuff)
        for i, item in enumerate(stuff):
            if isinstance(item, str):
                _all[i] = item.encode(encoding)
            elif not isinstance(item, bytes): # another iterable
                new = []
                for inner in item:
                    if isinstance(inner, str):
                        inner = inner.encode(encoding)
                    new.append(inner)
                _all[i] = new
        return _all

    # this is the re-implementation of the built-in print function
    # we use this later for printing to screen
    # we can override the default function in the outer scope
    def _print(self, *out, enc=None, file=None, sep=None, end=None, spl=True):
        """Safe way to print to screen or to a file.

        This mimics the built-in print() behaviour and adds versatility.
        This can be used directly, or tweaked for additional functionality."""

        if enc is None:
            enc = self.encoding
        elif not isinstance(enc, str):
            raise TypeError("invalid type provided for encoding")

        if file is None:
            if self.file is None:
                file = self.fb_file
            else:
                file = self.file
        elif isinstance(file, bytes):
            file = file.decode(enc)
        elif not _is_file_or_desc(file):
            raise TypeError("invalid file object")

        if sep is None:
            sep = self.separator
        elif not isinstance(sep, (str, bytes)):
            raise TypeError("expected str or bytes, got %r" % _get_type(sep))

        if end is None:
            end = self.ending
        elif not isinstance(end, (str, bytes)):
            raise TypeError("expected str or bytes, got %r" % _get_type(end))

        lout = list(out)

        for i, line in enumerate(out):
            if isinstance(line, bytes):
                lout[i] = line.decode(enc)
            elif not isinstance(line, str):
                lout[i] = repr(line)

        if spl:
            lout = self._split_lines(lout, enc, sep, end)

        # create a file object handler to write to.
        # if 'file' has a write() method, don't ask questions and use it
        # it's up to the end user if that method fails.
        # let's be careful though, as this can be fed its own instance;
        # this will work safely on itself, but make sure to avoid recursion.
        # as such, .write() needs to not be able to call this function,
        # otherwise this would lead to an infinite recursive loop
        if hasattr(file, "write"):
            # make sure it can be called, and not just a random name
            if callable(file.write):
                objh = file
            else:
                raise TypeError("error: object is not writable")
        else:
            # if it is str/bytes, it will be a file on the hard drive.
            # open it, but don't truncate the file; instead append to it.
            # if it's not a string, it's an int, since we did checks earlier;
            # therefore, allow the opening, but make sure not to close it
            # as it can be sys.stdout; it's up to the user to make sure it
            # frees up the resources properly in that case
            if isinstance(file, (str, bytes)):
                objh = open(file, "a", errors="replace")
            else: # int
                objh = open(file, "w", errors="replace", closefd=False)

        if isinstance(sep, bytes):
            sep = sep.decode(enc)

        if isinstance(end, bytes):
            end = end.decode(enc)

        objh.write(sep.join(lout) + end) # mimic built-in print() behaviour

        # instead of asking for it, flush the stream if we can
        if hasattr(objh, "flush"):
            objh.flush()

        # close the used resources if we can, again no need to ask for it
        if hasattr(objh, "close"):
            objh.close()

    def _get_output(self, out, sep, end):
        """Sanitizes output and performs checks for bytes objects."""
        out, sep, end = self._make_all_equal(out, sep, end)
        if not out: # called with no argument, let's support it anyway
            out = ['']
        _lns = ("", "\n")
        if isinstance(sep, bytes):
            _lns = (b"", b"\n")
        msg = None
        for line in out:
            if msg is None:
                msg = line
            else:
                if line == _lns[0]:
                    line = _lns[1]
                msg = msg + sep + line
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

        Default:    {}

    ignorers:       Dictionary of {setting:type} pairs. This can be used when
                    instantiating the class to allow more customization over
                    various calls, to ignore certains settings for certtain
                    types. This will internally set the setting to False if
                    and when applicable. See 'bypassers' if you wish to use
                    any arbitrary value.

        Default:    {}

    bypassers:      Iterable of (setting, type, module, attr) iterables.
                    'setting' is the setting to bypass when 'type' matches the
                    type that the logger was called with. It will replace the
                    setting's value with the value of attribute 'attr' of
                    module or dict 'module'. If 'module' is None, 'attr' will
                    be used as its immediate value, without any lookup.

        Default:    ()
"""

    def __init__(self, encoding="utf-8", separator=" ", ending="\n",
                 file=None, use_utc=False, ts_format=("[%Y-%m-%d] " + 
                 "(%H:%M:%S UTC{tzoffset})"), display=True, write=True,
                 logfiles={}, ignorers={}, bypassers=()):

        BaseLogger.__init__(encoding, separator, ending, file, use_utc,
                            ts_format)

        self.display = display
        self.write = write

        self.logfiles = logfiles
        self.ignorers = ignorers

        # this needs to be list/tuple of (setting, type, module, attr) tuples
        # the setting is the setting to bypass; type is the type to check for
        # to determine if bypassing should occur; module and attr are used
        # with getattr() to bypass the value of setting with the one found
        # in the given module, for the given attribute
        self.bypassers = bypassers

    def logger(self, *output, file=None, type=None, display=None, write=None,
               sep=None, end=None, split=True, use_utc=None, ts_format=None):
        """Logs everything to screen and/or file. Always use this."""
        output = self._get_output(output, sep, end)
        timestamp = self._get_timestamp(use_utc, ts_format)
        # todo
