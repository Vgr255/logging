#!/usr/bin/env python3

"""Interpolation mechanism for translation and possibly others.

Help on creating specialized subclasses can be found in the docstring
of the Interpolater class. The module currently exposes the following:

- String: A subclass of Interpolater, with settings defined to be a
          superset of the str.format() interpolation mechanism. It has
          all the features that str.format() does, with some extras:

          - Support for negative delta (indexes) for tuples
          - Support for callables in format string

          Note about callables: the only supported callables are those
          provided as an argument (positional or keyword) to format()
          or format_map(), or methods of provided arguments.

"""

__all__ = ["String"]

import re

class Interpolater:
    """Base class for string interpolation.

    Subclasses may define the following class-level variables:

    'pattern': A regex object as returned by 're.compile'. It will be
               used to check for the matching in the string. If set to
               None, .format() will always return the string unchanged.

    'ignore': A two-tuple, where the first item is a regex object,
              which will be used to determine that a certain part of
              the string should not be interpolated. The second item
              should be a slice object, which will be used as a
              subscript to the string. Use slice(None) to keep the
              same string. The 'ignore' variable may also be None.

    'conversion': A two-tuple composed of a regex and slice objects.
                  The regex object will be used to find the conversion
                  part of the string (if any). Note that the prefix or
                  suffix need to be included in this. The slice object
                  will be used to remove them. The variable may also be
                  set to None, whereas no conversion will be assumed.

    'specifier': A two-tuple, with the first item being a regex object,
                 which will be used to determine the format specifier,
                 if any. Note that the interpolater will start parsing
                 the format specifier as soon as this matches, so make
                 sure to include the character(s) to indicate the
                 beginning. The second item is a slice that will be
                 used to remove the specifier prefix/suffix from the
                 format specifier. If this variable is set to None, no
                 specifier will be assumed.

    'bounds': A slice object used to remove the parts of the string
              that shouldn't be used in the replacement (so that e.g.
              "{foo}" becomes "foo" - the braces will still be removed
              from the final string in this example).

    The order of the format specifier or the conversion syntax does not
    matter, as they will be parsed regardless of which comes first.

    """

    pattern = None
    ignore = None
    conversion = None
    specifier = None
    bounds = slice(None)

    def __init__(self, string):
        """Create a new instance for interpolation."""
        self.string = string

    def __repr__(self):
        """Return the exact representation of self."""
        try:
            return "{self.__class__.__name__}({self.string!r})".format(self=self)
        except RecursionError:
            return "{self.__class__.__name__}(<...>)".format(self=self)

    def __str__(self):
        """Return the string of self."""
        return str(self.string)

    def __format__(self, format_spec=""):
        """Return a formatted string of self."""
        if not format_spec:
            return self.string
        raise NotImplementedError("__format__ is not yet implemented")

    def format(*args, **kwargs):
        """Return a formatted string using the given arguments."""
        if not args:
            raise TypeError("format() needs an argument")
        self, *lst = args
        kwargs.update(enumerate(lst))
        kwargs[None] = len(lst)
        return self.format_map(kwargs)

    def format_map(self, mapping):
        """Return a formatted string using the mapping directly.

        The mapping may contain int keys, which will be used for the
        numbered positions in the format string. In that case, the
        mapping may contain a None key, with the associated value being
        the upper bound of the equivalent tuple of arguments (i.e. the
        length). This only matters in the cases where negative indexes
        are used. If the key is not present, no error will be raised
        and the negative index will be used as it would normally.

        Please note that no checking will be done against the mapping
        to make sure they contain the proper keys. Instead, an error
        will be raised when the missing key is accessed for the number
        keys, and a missing (or incompatible) None key will simply be
        ignored (and negative indexes subsequently left as-is).

        """

        # if self.pattern and self.ignore are both None, we could stop
        # here and return self.string already. however, in those cases,
        # the path taken will be very small (and fast), as it will only
        # create three lists, a regex pattern and a single integer. it
        # will also help with testing, by making sure that we don't add
        # any special cases, and instead let the format logic handle
        # everything the way it normally would. performance for the
        # formatting operations shouldn't be a concern. there are many
        # ways this code could be improved - one of them being support
        # for much more advanced regexes than the simple ones we do now

        count = -1
        parts = []
        ignore = []
        splitter = re.compile(r"[\(\)\[\]\.]")
        if self.ignore is not None:
            ignore_pattern, replace_slice = self.ignore
            ignore_part = []
            line = self.string
            match = ignore_pattern.search(line)
            while match:
                ignore_part.append(line[:match.start()])
                ignore_part.append(match.group())
                line = line[match.end():]
                match = ignore_pattern.search(line)

            if line:
                ignore_part.append(line)

            for i, line in enumerate(ignore_part):
                if i % 2:
                    parts.append(None)
                    ignore.append(line[replace_slice])
                else:
                    if self.pattern is not None:
                        part = []
                        match = self.pattern.search(line)
                        while match:
                            part.append(line[:match.start()])
                            part.append(match.group())
                            line = line[match.end():]
                            match = self.pattern.search(line)

                        if line:
                            part.append(line)

                        parts.append(part)
                        ignore.append(None)

                    else:
                        parts.append(None)
                        ignore.append(line)

        else:
            if self.pattern is not None:
                line = self.string
                part = []
                match = self.pattern.search(line)
                while match:
                    part.append(line[:match.start()])
                    part.append(match.group())
                    line = line[match.end():]
                    match = self.pattern.search(line)

                if line:
                    part.append(line)

                parts.append(part)
                ignore.append(None)

            else:
                parts.append(None)
                ignore.append(self.string)

        final = []

        for strings, ignored in zip(parts, ignore):
            if strings is None:
                final.append(ignored)
                continue

            for i, string in enumerate(strings):
                auto = False
                if not i % 2:
                    final.append(string)
                    continue

                string = string[self.bounds]

                specifier = conversion = None
                if self.specifier is not None:
                    spec_pattern, spec_slice = self.specifier
                    match = spec_pattern.search(string)
                    if match is not None:
                        specifier = match.group()
                        string = string[:match.start()]

                if self.conversion is not None:
                    conv_pattern, conv_slice = self.conversion
                    match = conv_pattern.search(string)
                    if match is not None:
                        conversion = match.group()
                        string = string[:match.start()]
                    elif specifier is not None:
                        match = conv_pattern.search(specifier)
                        if match is not None:
                            conversion = match.group()
                            specifier = specifier[:match.start()]

                if specifier is not None:
                    specifier = specifier[spec_slice]
                    string = format(type(self)(string), specifier)

                converter = str
                if conversion is not None:
                    conversion = conversion[conv_slice]
                    if conversion in ("s", "str"):
                        converter = str
                    elif conversion in ("r", "repr"):
                        converter = repr
                    elif conversion in ("a", "ascii"):
                        converter = ascii
                    else:
                        raise ValueError("Unknown conversion specifier: {!r}".format(conversion))

                seps = []
                match = splitter.search(string)
                while match:
                    if match.start():
                        seps.append(string[:match.start()])
                    seps.append(match.group())
                    string = string[match.end():]
                    match = splitter.search(string)

                if string:
                    seps.append(string)

                if seps:
                    string = seps.pop(0)

                if not string:
                    if count is None:
                        raise ValueError("cannot switch from manual field "
                              "specification to automatic field numbering")
                    count += 1
                    string = str(count)
                    auto = True

                if string.count("-") <= 1 and string.lstrip("-").isdigit():
                    if count is not None and count != -1 and not auto:
                        raise ValueError("cannot switch from automatic field "
                              "numbering to manual field specification")

                    if not auto:
                        count = None # prevent switching between automatic/manual

                    num = int(string)
                    if num < 0:
                        try:
                            num += mapping[None]
                        except (KeyError, TypeError):
                            pass # we just keep the number as-is

                    for value in (int(string), string, num):
                        try:
                            result = mapping[value]
                            break
                        except KeyError:
                            pass
                    else:
                        raise IndexError("Format index out of range")

                else:
                    result = mapping[string]

                res = [None] + seps
                i = 1
                while i < len(res):
                    sep = res[i]
                    assert sep is not None, "unexpected None in results index"
                    if sep == ".":
                        if res[i-1] is not None or len(res) <= i+1 or res[i+1] in "[]().":
                            raise ValueError("Invalid attribute access in format string")
                        result = getattr(result, res[i+1])
                        res[i] = res[i+1] = None
                        i += 2

                    elif sep == "[":
                        if len(res) > i+1 and res[i+1] == "]":
                            raise ValueError("Empty indexing in format string")
                        if res[i-1] is not None:
                            raise ValueError("Invalid indexing in format string")
                        s = 2
                        while i+s <= len(res):
                            if res[i+s] == "]":
                                break
                            s += 1
                        else:
                            raise ValueError("Invalid indexing in format string")

                        r = "".join(res[i+1:i+s])
                        result = result[r]
                        res[i:i+s+1] = [None] * (s+1)
                        i = i+s+1

                    elif sep == "(":
                        if res[i-1] is not None:
                            raise ValueError("Invalid call in format string")
                        s = 1
                        while i+s <= len(res):
                            if res[i+s] == ")":
                                break
                            s += 1
                        else:
                            raise ValueError("Invalid call in format string")

                        if s == 1: # no arguments
                            result = result()
                        else:
                            r = "".join(res[i+1:i+s])
                            result = result(r)
                        res[i:i+s+1] = [None] * (s+1)
                        i = i+s+1

                    else:
                        raise ValueError("Invalid operation in format string")

                final.append(converter(result))

        return "".join(final)

class String(Interpolater):
    """Interpolation system akin to str.format()."""

    pattern = re.compile("{[^{}]*}")
    ignore = re.compile("({{|}})"), slice(0, 1)
    conversion = re.compile("!.+"), slice(1)
    specifier = re.compile(":.+"), slice(1)
    bounds = slice(1, -1)
