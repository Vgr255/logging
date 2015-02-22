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
- Implement arbitrary string replacing from within another module
- Add ability to view docstrings properly (already implemented elsewhere)
"""

from datetime import datetime
import shutil
import time
import sys

def _is_file_or_desc(obj):
    """Returns True if obj is a file or file descriptor, False otherwise."""
    # we don't care what the obj is, if it has 'write' it's up to them
    # to implement it properly; str or int will have open() used on them
    return hasattr(obj, "write") or isinstance(obj, (str, int))

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
    """Base Logger class for inheritence."""
    def __init__(self, **kwargs):
        self.display = True
        self.write = True
        self.fb_file = sys.stdout
        self.file = None
        self.encoding = "utf-8"
        self.separator = " "
        self.ending = "\n"
        self.logfiles = {}
        self.ignorers = {}

        # this needs to be list/tuple of (setting, module, attr) tuples
        # the setting is the setting to bypass; module and attr are used
        # with getattr() to bypass the value of setting with the one found
        # in the given module, for the given attribute
        self.bypassers = ()
        self.use_utc = False

        # this can have {tzname} and {tzoffset} for formatting
        # this adds respectively a timezone in the format UTC or EST
        # and an offset from UTC in the form +0000 or -0500
        self.timestamp_format = "[%Y-%m-%d] (%H:%M:%S UTC{tzoffset})"

        self.__dict__.update(kwargs)

        # we need to have a general fallback file or file object
        # if we don't, raise an exception here instead of away from the source
        if not self.fb_file:
            raise Exception("no fallback file specified")

        if not _is_valid_encoder(self.encoding):
            raise TypeError("%r is not a valid encoding" % self.encoding)

        # all those type checkings are done to ensure we catch any error as
        # soon as possible, instead of having something blow up down the road;
        # the functions will expect a string and will fail if not given as such
        if isinstance(self.separator, bytes):
            self.separator = self.separator.decode(self.encoding)
        elif not isinstance(self.separator, str):
            raise TypeError("expected str, got %r" % _get_type(self.separator))

        if isinstance(self.ending, bytes):
            self.ending = self.ending.decode(self.encoding)
        elif not isinstance(self.ending, str):
            raise TypeError("expected str, got %r" % _get_type(self.ending))

    def _get_timestamp(self, use_utc=None, timestamp_format=None):
        """Returns a timestamp with timezone + offset from UTC."""
        if use_utc is None:
            use_utc = self.use_utc
        if timestamp_format is None:
            timestamp_format = self.timestamp_format
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

    def _split_lines(self, output, sep=" "):
        col = shutil.get_terminal_size()[0]
        if not isinstance(output, str):
            output = sep.join(output) # make any iterable work
        output = output.strip(" ")
        lines = output.split("\n")
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
    def _print(self, *output, encoding=None, file=None, sep=None, end=None, split=False):
        if encoding is None:
            encoding = self.encoding
        elif not isinstance(encoding, str):
            raise TypeError("invalid type provided for encoding")

        if file is None:
            if self.file is None:
                file = self.fb_file
            else:
                file = self.file
        elif isinstance(file, bytes):
            file = file.decode(encoding)
        elif not _is_file_or_desc(file):
            raise TypeError("invalid file object")

        if sep is None:
            sep = self.separator
        elif isinstance(sep, bytes):
            sep = sep.decode(encoding)
        elif not isinstance(sep, str):
            raise TypeError("expected str, got %r" % _get_type(sep))

        if end is None:
            end = self.ending
        elif isinstance(end, bytes):
            end = end.decode(encoding)
        elif not isinstance(end, str):
            raise TypeError("expected str, got %r" % _get_type(end))

        lout = list(output)

        for i, line in enumerate(output):
            if isinstance(line, bytes):
                lout[i] = line.decode(encoding)
            elif not isinstance(line, str):
                lout[i] = repr(line)

        if split:
            lout = self._split_lines(lout, sep)

        # create a file object handler to write to
        # if 'file' has a write() method, don't ask questions and use it
        # it's up to the end user if that method fails
        if hasattr(file, "write"):
            objh = file
        else:
            # if it is a string, it will be a file on the hard drive
            # open it, but don't truncate the file; instead append to it
            # if it's not a string, it's an int, since we did checks earlier
            # therefore, allow the opening, but make sure not to close it
            # as it can be sys.stdout; it's up to the user to make sure it
            # frees up the resources properly
            if isinstance(file, str):
                objh = open(file, "a", errors="replace")
            else: # int
                objh = open(file, "w", errors="replace", closefd=False)

        objh.write(sep.join(lout) + end) # mimic built-in print() behaviour

        # instead of asking for it, flush the stream if we can
        if hasattr(objh, "flush"):
            objh.flush()

        # close the used resources if we can, again no need to ask for it
        if hasattr(objh, "close"):
            objh.close()
