#!/usr/bin/env python3

"""Patterns and parsers for various purposes."""

__all__ = ["FormatSpecifierParser"]

import re

class FormatSpecifierParser:
    """Parser for the format specifiers used in the Interpolater."""

    parse_format_spec = re.compile(

    r"""
    \A
    (?:
        (?P<fill>.)?
        (?P<align>[<>=^])
    )?
    (?P<sign>[-+ ])?
    (?P<alt>\#)?
    (?P<zeropad>0)?
    (?P<width>(?!0)\d+)?
    (?P<sep>,)?
    (?:\.(?P<precision>0|(?!0)\d+))?
    (?P<type>[eEfFgGn%])?
    \Z
    """,

    re.VERBOSE | re.DOTALL)

    def __init__(self, format_spec, *, is_digit):
        """Parse a format specifier and store attributes to self."""

        match = self.parse_format_spec.match(format_spec)
        if match is None:
            raise ValueError("Invalid format specifier: {!r}".format(format_spec))

        match_dict = match.groupdict()

        self.fill = match_dict["fill"]
        self.align = match_dict["align"] or (is_digit and ">" or "<")

        self.zeropad = (match_dict["zeropad"] is not None)

        if self.zeropad:
            if self.fill is not None and self.fill != "0":
                raise ValueError("Fill character conflicts with format specifier"
                                 ": {!r}".format(format_spec))

            if self.align is not None and self.align != ">":
                raise ValueError("Alignment conflicts with format specifier"
                                 ": {!r}".format(format_spec))

            self.fill = "0"
            self.align = ">"

        self.fill = self.fill or " "

        self.width = int(match_dict["width"] or 0)

        if self.align == "=" and not is_digit:
            raise ValueError("'=' not allowed in string format specifier")

        self.sign = match_dict["sign"]

        if self.sign is not None and not is_digit:
            raise ValueError("Sign not allowed in string format specifier")

        self.alt = match_dict["alt"]

        if self.alt is not None and not is_digit:
            raise ValueError("Alternate form (#) not allowed in string format specifier")

        self.width = match_dict["width"]
        self.sep = match_dict["sep"]
        self.precision = match_dict["precision"]
        self.type = match_dict["type"]
