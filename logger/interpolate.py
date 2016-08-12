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

from typing import Optional, Tuple, Pattern

class Interpolater:
    """Base class for string interpolation.

    Subclasses may define the following class-level variables:

    'pattern': A regex object as returned by 're.compile'. It will be
               used to check for the matching in the string. If set to
               None, .format() will always return the string unchanged.
               It is the responsibility of the subclasses creators to
               make sure that the regex is powerful enough to match all
               the desired cases, while not matching the undesired ones
               (the String subclass is a good example of doing this).

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

    Note: The format specifier and the conversion syntax in the string
    do not have a specified ordering; both will be parsed regardless.

    You may also define the following functions:

    'bounds': This will be called with the string to replace (i.e. the
              matching part of the pattern). It should return a string,
              which will then be used to look up the arguments in the
              tuple and/or mapping. The default function on the base
              class returns the string unchanged.

    'modifier': This function or method will be called with a list of
                all the substrings that will be part of the final
                string (after all interpolation has been done, and just
                before returning it). It should return a string, which
                the caller will receive. The default behaviour is to
                return the result of ''.join(final_list).

    'check': This will be passed two lists; the first is the list of
             substrings matching the pattern, but before they they get
             interpolated. The second list contains the substrings
             which don't match the pattern. The indexes follow up from
             across the lists (i.e. they are unique), so if there is a
             match at the beginning of the string, the first list will
             contain said match as index 0, and the second list will
             have None at position 0. This is used to track the order
             of the substrings. The return code of the function is not
             checked against, but exceptions will propagate unharmed to
             the caller, and mutations to the lists will be reflected
             in the interpolation (although there are guards against
             invalid mutation). This can also be used to modify the
             second list to special-case some sequences of characters,
             for example modify "{{" and "}}" to "{" and "}" (in the
             case of String).

    Note on creating subclasses:

    All methods can be overridden in the subclasses. The only methods
    which don't make sense to be overridden are format and format_map.
    All of the other methods (e.g. __init__, __len__, __str__ ...) can
    be safely overridden. The format and format_map methods delegate to
    the methods for their operation. The 'string' attribute is only
    used in __init__, __len__, __str__ and __repr__; the interpolation
    methods call len(self) and str(self) to get the length and string
    of self, instead of accessing the 'string' member.

    Note on the return type of format() (and format_map()):

    The formatting methods will return exactly what is returned by the
    modifier method on the object -- subclasses which desire to have an
    alternative return type can override the default behaviour in that
    method. The default return type is 'str'.

    """

    pattern = None # type: Optional[Pattern[str]]
    conversion = None # type: Optional[Tuple[Pattern[str], slice]]
    specifier = None # type: Optional[Tuple[Pattern[str], slice]]

    def bounds(self, string):
        """Return the string with proper bounds."""
        return string

    def modifier(self, final):
        """Join the string and return it."""
        return "".join(final)

    def check(self, lines, ignored):
        """Check the output and apply special cases."""

    def __init__(self, string):
        """Create a new instance for interpolation."""
        self.string = str(string)

    def __len__(self):
        """Return the length of the string."""
        return len(str(self))

    def __repr__(self):
        """Return the exact representation of self."""
        try:
            return "{self.__class__.__name__}({self.string!r})".format(self=self)
        except RecursionError:
            return "{self.__class__.__name__}(<...>)".format(self=self)

    def __str__(self):
        """Return the string of self."""
        try:
            return str(self.string)
        except RecursionError:
            raise RecursionError("maximum recursion depth reached while "
                  "calling a Python object") from None

    def __format__(self, format_spec=""):
        """Return a formatted string of self."""
        if not format_spec:
            return str(self)
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

        To use keyword and positional names, the format() method is the
        recommended way. It will prepare the mapping and call this
        method. If a custom mapping (e.g. defaultdict) needs to be used
        for various purposes, the caller is responsible for properly
        filling the mapping with the relevant information. A malformed
        mapping (for example, 'defaultdict(lambda: 42)') is considered
        to be a user error, and is not guarded against. The consenting
        adults rule applies here as well.

        """

        # TODO: 'invalid' class variable for e.g. unmatched braces
        # also better handle double braces (not at the end)

        if self.pattern is None:
            return str(self)

        count = -1
        lines = []
        ignore = []
        splitter = re.compile(r"[\(\)\[\]\.]")

        last = 0
        line = str(self)
        for match in self.pattern.finditer(line):
            if match.start() > last:
                ignore.append(line[last:match.start()])
                lines.append(None)

            ignore.append(None)
            lines.append(match.group())

            last = match.end()

        if last < len(self):
            ignore.append(line[last:])
            lines.append(None)

        for a, b in zip(lines, ignore):
            assert (a is None) ^ (b is None)

        self.check(lines, ignore)

        final = []

        for string, ignored in zip(lines, ignore):
            if string is None:
                if ignored is None or not isinstance(ignored, str):
                    raise ValueError("invalid mutation in {0}.check".format(
                                     type(self).__name__))
                final.append(ignored)
                continue

            if ignored is not None or not isinstance(string, str):
                raise ValueError("invalid mutation in {0}.check".format(
                                 type(self).__name__))
            string = self.bounds(string)

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
            last = 0
            for match in splitter.finditer(string):
                if last != match.start():
                    seps.append(string[last:match.start()])
                seps.append(match.group())
                last = match.end()

            if last < len(string):
                seps.append(string[last:])

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
                    while i+s < len(res):
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
                    while i+s < len(res):
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

            assert res.count(None) == len(res) == i
            final.append(converter(result))

        result = self.modifier(final)
        if not isinstance(result, str):
            raise ValueError("{0}.modifier must return a str, not {1}".format(
                             type(self).__name__, type(result).__name__))
        return result

class String(Interpolater):
    """Interpolation system akin to str.format()."""

    def bounds(self, string):
        """Remove the braces from the string."""
        return string[1:-1]

    def check(self, lines, ignored):
        """Change double braces to single ones."""
        single = re.compile("({|})")
        double = re.compile("({{|}})")
        for i, line in enumerate(ignored):
            if double.search(line):
                ignored[i] = line.replace("{{", "{").replace("}}", "}")
            elif single.search(line):
                raise ValueError("Single {!r} encountered in format string".format(single.search(line).group()))

    pattern = re.compile("(?<!{){[^{}]*}(?!})")
    conversion = re.compile("!.+"), slice(1)
    specifier = re.compile(":.+"), slice(1)
