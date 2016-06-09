#!/usr/bin/env python3

"""Logging module for the specific needs and corner cases.

This supports translation (via the 'interpolate' submodule) when used
with the 'Translater' subclass, as well as the bypassing of certain
settings based on external variables (via the 'bypassers' submodule).

"""

__author__ = "Emanuel 'Vgr' Barry"

__version__ = "0.2.3" # Version string not being updated during refactor
__status__ = "Mass Refactor"

__all__ = ["TypeLogger", "TranslatedTypeLogger",        # type-based loggers
           "LevelLogger", "TranslatedLevelLogger",      # level-based loggers
           "NamesLogger", "TranslatedNamesLogger",      # names-based loggers
          ]

from datetime import datetime
import shutil
import types
import time
import sys
import re

from . import bypassers as bp_module

from .decorators import handle_bypass, check_bypass
from .utilities import pick

class BaseLogger:
    """Base Logger class for your everyday needs.

    This can be inherited to create custom classes.
    This is not user-faced. For general purposes, please use the Logger
    class. All arguments have a default value of None, and their stated
    default value is assigned after the call. This can be used to pass
    None for a parameter to ensure it always uses the correct default
    value, should it change. Subclasses defined in this module follow
    this rule, and any other class subclassing it should follow it too.
    It is also recommended that any method defined under such classes
    follow this rule, although it is not strongly enforced.

    sep:
                    String to be used to join the lines together.

        Default:    " "

    use_utc:
                    Boolean value to determine if the timestamps should
                    use Universal Coordinated Time or the local time.

        Default:    False

    display:
                    Default parameter to determine if the loggers
                    should print to screen. This can be overriden when
                    calling the method, on a per-line basis.

        Default:    True

    write:
                    Default parameter to determine if the loggers
                    should write to a file. This can be overriden when
                    calling the method, on a per-line basis.

        Default:    True

    ts_format:
                    Format string for timestamps. The parameters are
                    the same as the time module's 'strftime' function.
                    However, for the time zone name and offset, use
                    {tzname} and {tzoffset} respectively. This is done
                    to account for the use_utc parameter as well as
                    allow full cross-platformity (some platforms, such
                    as certain versions of Windows, fail to interpret
                    %z properly). The timezone name will be the
                    three-letters abbreviation of the timezone,
                    uppercased. The time zone offset is a string with
                    + or - following by 4 digits, like +0000 or -0500,
                    the digits being HHMM.

        Default:    "[%Y-%m-%d] (%H:%M:%S {tzoffset})"

    print_ts:
                    Boolean value to determine whether the timestamps
                    should be printed to screen as well as to files.

        Default:    False

    split:
                    Boolean value to determine if long lines should be
                    split when printing to screen.

        Default:    True

    bypassers:
                    This is an iterable of (setting, types, pairs,
                    module, attr) iterables. 'types' is an iterable of
                    all types that can match this bypasser. 'pairs' is
                    an iterable of two-tuples, the first argument is
                    the module, a dictionary or None, the second
                    argument is the attribute to search for in the
                    module or dict; if the module is None, the
                    bypassers will use the attribute as its direct
                    value look-up. After this mangling, if the value is
                    True in a boolean context, then the override will
                    occur, and the setting's value will be overridden
                    by the module and attribute's look-up, in the same
                    way that the pairs are check for truth testing.
                    'setting' is the setting to bypass when the
                    previously-mentioned conditionals evaluate to True,
                    so if at least one of the types matches the type
                    that the logger was called with, or if the value
                    evaluates to True. Do note that the types and pairs
                    parameters expect sets as parameters, and will fail
                    if not given as such. They can, however, be any
                    other object with the same API as sets. This is
                    done to allow the values to be modified and for the
                    modifications to carry over to the bypassers. Do
                    note that this parameter expects an iterable of
                    five-tuples, or an empty iterable.

        Default:    See below

    Available settings for the bypassers:

    These are the available settings to bypass. Do note that the
    default of all these settings is to not do anything, and must be
    explicitely set otherwise.

    "timestamp":
                    Will be used to replace the standard timestamp when
                    writing to file. It will not use that value to
                    perform the timestamp getting operation. Rather, it
                    will use the string given directly. If a different
                    timestamp for various reasons is the desired
                    result, a manual call to the _get_timestamp method
                    will need to be done. This is typically used to
                    remove a timestamp, so it will be used with the
                    pair of (None, ''), effectively removing the
                    timestamp.

    "splitter":
                    This will be used to determine if clever splitting
                    should occur when printing to screen. Clever
                    splitting splits the line at the latest space
                    before the line gets to the end of the terminal's
                    length. By default, this is True, and can be
                    changed when calling, on a per-line basis. This
                    bypasser overrides that.

    "display":
                    This is used to override the per-line setting that
                    decides whether the line should be printed to the
                    screen. This is set to True by default, and can be
                    overriden when calling on a per-line basis. This
                    bypasser can be used to bypass this setting.

    "write":
                    This is used to override the per-line setting that
                    decides whether the line should be written to the
                    file or not. This is set to True by default, and
                    can be overriden when calling on a per-line basis.
                    This bypasser can override that parameter.

    """

    def __init__(self, *, sep=None, use_utc=None, ts_format=None,
                       print_ts=None, split=None, bypassers=None,
                       display=None, write=None, encoding=None,
                       errors=None, end=None, **kwargs):
        """Create a new base instance."""

        super().__init__(**kwargs)

        self.separator = pick(sep, " ")
        self.encoding = pick(encoding, "utf-8")
        self.errors = pick(errors, "surrogateescape")
        self.end = pick(end, "\n")

        self.display = pick(display, True)
        self.write = pick(write, True)

        self.use_utc = pick(use_utc, False)
        self.print_ts = pick(print_ts, False)
        self.split = pick(split, True)

        try:
            func = self._bp_handler
        except AttributeError:
            func = bp_module.BaseBypassers

        self.bypassers = func.from_iterable(bypassers)
        self.bypassers.add("timestamp", "splitter", "display", "write")

        # this can have {tzname} and {tzoffset} for formatting
        # this adds respectively a timezone in the format UTC or EST
        # and an offset from UTC in the form +0000 or -0500
        self.ts_format = pick(ts_format, "[%Y-%m-%d] (%H:%M:%S {tzoffset})")

    @handle_bypass
    def _get_timestamp(self, use_utc=None, ts_format=None):
        """Return a timestamp with timezone + offset from UTC."""
        use_utc = pick(use_utc, self.use_utc)
        ts_format = pick(ts_format, self.ts_format)

        if not ts_format or "timestamp" in self.bypassed:
            return self.bypassed.get("timestamp", "")

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
        return tmf.format(tzname=tz, tzoffset=offset).strip().upper()

    def _split_lines(self, out):
        """Split long lines at clever points."""
        col = shutil.get_terminal_size().columns
        lines = [line.rstrip(" ") for line in out.splitlines()]
        splines = [line.split(" ") for line in lines]
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
                if len(new) >= col and word != new:
                    newlines.append(newstr)
                    newstr = word
                elif len(new) >= col and word == new:
                    if newstr:
                        newlines.append(newstr)
                    newlines.append(new)
                    newstr = ""
                else:
                    newstr = new
            if newstr:
                newlines.append(newstr)
        return "\n".join(newlines)

    @handle_bypass
    def _print(self, *output, sep=None, use_utc=None, ts_format=None,
                     print_ts=None, encoding=None, split=None,
                     errors=None, end=None):
        """Print to screen and remove all invalid characters."""

        sep = pick(sep, self.separator)
        encoding = pick(encoding, self.encoding)
        errors = pick(errors, self.errors)
        end = pick(end, self.end)

        output = self._get_output(output, sep)

        if pick(print_ts, self.print_ts):
            out = output.splitlines()
            ts = self._get_timestamp(use_utc, ts_format)
            for i, line in enumerate(out):
                out[i] = " ".join((ts, line))
            output = "\n".join(out)

        if self.bypassed.get("splitter", pick(split, self.split)):
            output = self._split_lines(output)

        with open(sys.stdout.fileno(), "w", errors=errors,
                  encoding=encoding, closefd=False) as file:

            file.write(output + end)

            file.flush()

    def _get_output(self, output, sep):
        """Sanitize output and join iterables together."""
        return sep.join(str(x) for x in output)

    def _get_output_list(self, output):
        """Sanitize output and return a list of lines."""
        return [str(x) for x in output] or ['']

    @check_bypass
    def logger(self, *output, sep=None, file=None, split=None,
               use_utc=None, ts_format=None, print_ts=None,
               display=None, write=None, encoding=None, errors=None):
        """Base method to make sure it always exists."""
        output = self._get_output(output, pick(sep, self.separator))
        encoding = pick(encoding, self.encoding)
        errors = pick(errors, self.errors)
        display = pick(display, self.display)
        write = pick(write, self.write)

        if display:
            self._print(output, sep=sep, use_utc=use_utc, ts_format=ts_format,
                                print_ts=print_ts, split=split, errors=errors)

        if write and file is not None:
            with open(file, "a", encoding=encoding, errors=errors) as f:
                f.write(output + "\n")

    def docstring(self, *output, tabs=4, display=True, write=False, sep=None,
                        **rest):
        """Print a docstring using proper formatting."""
        newlined = False
        indent = None
        lines = []

        sep = pick(sep, "\n")

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

        self.logger(*lines, display=display, write=write, sep=sep, **rest)

class TypeLogger(BaseLogger):
    """Type-based logger class.

    The options are the same as the base class, with these additions:

    logfiles:
                    Dictionary of {type:file} pairs. The type is the
                    logging type that the logger expects. The file is
                    the file that tells the logger to write to. This
                    can be used for dynamic file logging.

        Default:    {"normal": "logger.log", "all": "mixed.log"}

    Additions to the bypassers:

    "logall":
                    Defaulting to None, this setting's bypassed value
                    must be a string object, which, if the bypassing
                    occurs, will be the file to write everything to.

    The following parameters are not actual bypassers. Only the types
    bound to the setting are of relevance. The pairs are ignored, and
    so are the module and attribute.

    "files":
                    The types bound to this setting will be used to
                    determine when to write and not to write to certain
                    files. This is only used when using the
                    Logger.multiple method, which will write to all
                    files specified, except those bound to the types
                    of this bypasser.

    "all":
                    The types bound to this setting will not be written
                    as when writing to the file defined through the
                    'logall' bypasser, if available.

    """

    def __init__(self, *, logfiles=None, **kwargs):
        """Create a new type-based logger."""

        super().__init__(**kwargs)

        files = {"normal": "logger.log"}

        if logfiles is not None:
            self.logfiles = logfiles
            for type, file in files.items():
                # if the type is already defined, don't overwrite it
                # only add to it if it doesn't exist
                self.logfiles[type] = self.logfiles.get(type, file)
        else:
            self.logfiles = files

        self.bypassers.add("logall", "files", "all")

    @check_bypass
    def logger(self, *output, file=None, type=None, display=None, write=None,
               sep=None, split=None, use_utc=None, ts_format=None,
               print_ts=None, encoding=None, errors=None, **kwargs):
        """Log everything to screen and/or file. Always use this."""

        sep = pick(sep, self.separator)
        encoding = pick(encoding, self.encoding)
        errors = pick(errors, self.errors)
        split = self.bypassed.get("splitter", pick(split, self.split))
        display = self.bypassed.get("display", pick(display, self.display))
        write = self.bypassed.get("write", pick(write, self.write))

        timestamp = self._get_timestamp(use_utc, ts_format)
        # this is the file to write everything to
        logall = self.bypassed.get("logall")

        if display:
            self._print(*output, sep=sep, use_utc=use_utc, split=split,
                        ts_format=ts_format, print_ts=print_ts, errors=errors)
        if write:
            output = self._get_output(output, sep).splitlines()
            alines = [x for x in self.logfiles if x in
                                 self.bypassers("all")[0]]
            getter = [file]
            if logall:
                getter.append(logall)
            for log in getter:
                if (log == logall and type not in alines) or log is None:
                    continue
                atypes = "type.{0} - ".format(type) if log == logall else ""
                with open(log, "a", encoding=encoding, errors=errors) as f:
                    for writer in output:
                        f.write("{0}{1}{2}\n".format(timestamp, atypes, writer))

    def multiple(self, *output, types=None, display=None, **rest):
        """Log one or more line to multiple files."""
        types = pick(types, ["normal"])

        if len(types) == 1 and "*" in types: # allows any iterable
            for log in self.logfiles:
                if log not in self.bypassers("files")[0]:
                    if display:
                        self.logger(*output, type=log, display=True, **rest)
                        display = False # display only once
                    else:
                        self.logger(*output, type=log, display=False, **rest)

        elif types:
            for log in types:
                if display:
                    self.logger(*output, type=log, display=True, **rest)
                    display = False
                else:
                    self.logger(*output, type=log, display=False, **rest)

        else:
            self.logger(*output, display=display, **rest)

    def show(self, *output, type="show", display=True, write=False, **rest):
        """Explicit way to only print to screen."""
        self.logger(*output, type=type, display=display, write=write, **rest)

class Translater(BaseLogger):
    """Logging class to use to translate lines.

    This is inherited from the BaseLogger class.
    This needs to be used in multiple inheritence to work properly.
    The parameters are the same as for the base class, plus these:

    all_languages:
                    Dictionary of {language:short} pairs. The language
                    is used for the standard lookup of the language.
                    The value is the 2-characters abbreviation of the
                    language. The default value is "English" for the
                    key, and "en" for the value. This must contain all
                    languages that this class will be asked to
                    translate to, see below for restrictions.

        Default:    {"English": "en"}

    check:
                    Boolean value that will determine if a line should
                    be checked for translation or not. If False, the
                    line will not be checked and will be printed or
                    writen to the file as-is

        Default:    True

    main:
                    The main language that will be used. This is
                    considered the "default" language, and is the one
                    that will be used to write to the normal files. It
                    will always be written to the files, no matter what
                    language is being used.

        Default:    "English"

    current:
                    The current language, used for translating and
                    printing to screen. When writing to one or more
                    files, the files that this language's lines are
                    written into will be prepended with the
                    two-characters short language abbreviation that was
                    given in the all_languages dict, followed by a
                    single underscore and the file's name. This will
                    not be done if the language is the same as 'main'.

        Default:    "English"

    module:
                    The module or dictionary where the translations
                    will be looked up. This can be any arbitrary
                    object, as long as either the object has an
                    attribute corresponding to the line to translate
                    (see below for information on how those are looked
                    up), or it implements indexing via module[attr] and
                    'attr' is in object 'module'. If both are true,
                    only the first will be used. If neither are true,
                    it will print the string as-is. It will never
                    error. It WILL error, however, if the language used
                    is not in 'all_languages'. If it is None, then the
                    'modules' argument will be checked instead, see
                    below. It will also be checked if the module
                    defined here fails to find the appropriate line.

        Default:    None

    modules:
                    If the above parameter is set to None or otherwise
                    fails, it will use this parameter instead. It is a
                    mapping of {language:module} pairs that will be
                    used to search for each language. The keys must be
                    in the all_languages mapping as well. The value
                    must be a module (or any object) where the
                    attributes or items are equivalent to the strings
                    that will be passed in. If both the above and this
                    parameter are None, no translating will occur.

        Default:    None

    first:
                    Determines which, of the line or the language, must
                    be checked first when looking up the translations.
                    The only valid arguments are "line" and "language".
                    Using 'line', the translater will look into the
                    module or mapping for an attribute or item named
                    'line', and then will look for an attribute or item
                    named like the current language, and will return
                    the matching result. Otherwise, it will look for an
                    item named like the current language, and then for
                    an item named like the line in it. If 'module' is
                    left undefined or fails but 'modules' is, this
                    parameter will be ignored and a single value lookup
                    will be performed.

                    Note about custom objects: The lookup uses getattr
                    followed by item.get if the former fails, falling
                    back to printing the line as-is if it fails.

        Default:    "language"

    pattern:
                    Regex pattern that determines when a line should be
                    given to the translater for replacing. If a line
                    doesn't match, it will not be translated.

        Default:    "^[A-Z0-9_]+$" - UPPERCASE_UNDERSCORED_NAMES

    Note on ignoring translation for certain lines: To prevent certain
    lines from being translated, use the "translate" setting for the
    bypassers, passing a five-tuple with the first item being
    "translate". The second item is an iterable (a set is the supported
    and recommended type) of types that should not be translated. The
    third item is another iterable (again, the Bypassers are meant to
    support a set), consisting of (module, attr) pairs, where the
    module can be any object or None, and the attribute can be an
    attribute or item of the module or, if the module is None, the
    direct value will be looked up instead. The last two parameters can
    be anything (but must be present), they will be replaced at runtime
    as they are only used internally to decide when not to translate.

    To entirely prevent any line from being checked against the pattern
    and be potentially translated, pass the "check" keyword argument
    with a True value, or use the "check" setting of the bypassers.

    Note on translating: The translated lines can take new-style
    formatting with {0} or similar; it can use list indexes, regular
    indexes or named indexes like {foo}. Assign an ordered iterable for
    the numeric indexes to the 'format' argument of the logger method,
    and a mapping to the 'format_dict' argument of the logger method.
    Old-style formatting using the modulus (%) operand may still be
    used, by passing a sequence or mapping to the 'format_mod' argument
    of the logger method. It is up to the user to make sure that the
    proper type of iterable is given, with the proper arguments in the
    string. Numerical and named arguments cannot be mixed for old-style
    formatting. The new-style formatting is the recommended method.
    Unlike new-style formatting, the modulus method can fail if the
    incorrect amount of parameters are given. Both formatting methods
    can be used at the same time. Also, do note that it IS possible to
    give strings matching the regex pattern to format, and they will be
    properly translated as well. It is not, however, possible to loop
    through these recursively. The formatting rules would become too
    complicated for the small benefit that such a feature would
    provide. If one really needs to do so, they can call the logger
    method recursively on their own.

    Worth of note: The modulus-style formatting is applied after the
    new-style formatting. This makes it easier to go one layer deeper
    into the formatting, and allow for formatting from inside the
    previsouly-formatted lines.

    If translating directly without using the logger method, here are a
    few useful bits of information:

    - It operates through side-effect. This means that it doesn't
      return any value, rather, it directly alters the list given. If
      the object passed in as the first parameter is not mutable, an
      exception will occur. This restriction does not apply to the
      formats.

    - It takes five arguments (besides self). The first argument is
      the mutable object used for the output (and which will be
      altered). The second argument is the language. This will be used
      for looking up which line lines to use. The 3 other arguments are
      used for formatting, post-translation. All 3 arguments must be
      given. The first of the three is to be used as the numerical
      formatting using new-style string formatting (the str.format
      method). The second is a mapping to be used in the new-style
      formatting as well. The third one can be either a (mutable)
      sequence or mapping, and is used for old-style formatting
      (modulus formatting with the % operand). It will be applied after
      the new-style formatting has been applied.

    - It makes sure to retain the original class of the formats
      iterables passed in, if it can. The class of each variable needs
      to define a copy method, if it does, it will be used. If there
      are no copy methods, it will use the default expectation of what
      the iterable should be; a list for 'format' and 'format_mod', and
      a dict for 'format_dict'; this is done to accept any object, not
      just built-in ones.

    """

    def __init__(self, *, main=None, current=None, module=None, modules=None,
                 first=None, pattern=None, all_languages=None, check=None,
                 **kwargs):
        """Create a new translater object."""

        super().__init__(**kwargs)

        self.main = pick(main, "English")
        self.current = pick(current, self.main)

        langs = {"English": "en"}

        if all_languages is not None:
            self.all_languages = all_languages
            for long, short in langs.items():
                self.all_languages[long] = self.all_languages.get(long, short)
        else:
            self.all_languages = langs

        self.check = pick(check, True)

        self.module = module
        self.modules = modules

        self.first = pick(first, "language")
        self.pattern = re.compile(pick(pattern, "^[A-Z0-9_]+$"))

        self.bypassers.add("check", "translate")
        self.bypassers.update(("translate",) +
                self.bypassers("translate")[:-2] + (None, True))

    def translate(self, output, language, format, format_dict, format_mod):
        """Translate a line into the desired language."""

        def copy(name, new):
            return getattr(name.__class__, "copy", new)(name)

        format = copy(format, list)
        format_dict = copy(format_dict, dict)

        if isinstance(format_mod, tuple):
            format_mod = list(format_mod)
        else: # TODO: support dict or drop support altogether. perhaps add our own interpolation mechanism
            format_mod = [str(format_mod)]

        def enum(iterable):
            if hasattr(iterable, "items"):
                return list(iterable.items())
            return enumerate(iterable)

        def get_line(module, other, fallback):
            try:
                value = module[other]
            except (TypeError, KeyError, IndexError):
                try:
                    value = getattr(module, other)
                except AttributeError:
                    return fallback
            return value

        for iterable in (format, format_dict, format_mod, output):
            for i, line in enum(iterable):
                if self.pattern.search(line) is None:
                    continue
                original = line
                module = None
                lang = None
                if self.module is not None:
                    if self.first == "line":
                        module = get_line(self.module, line, original)
                    else:
                        module = get_line(self.module, language,
                                 get_line(self.module, self.main, original))

                if module is None and self.modules is not None:
                    lang = self.modules.get(language)
                    if lang is not None:
                        module = get_line(lang, line, original)

                if module is not None:
                    if lang is None:
                        if self.first == "line":
                            line = get_line(module, language,
                                   get_line(module, self.main, original))
                        else:
                            line = get_line(module, line, original)

                    else:
                        line = module

                if line != original and iterable == output:
                    format_mod = tuple(format_mod)
                    line = line.format(*format, **format_dict) % format_mod

                iterable[i] = line

    @check_bypass
    def logger(self, *output, file=None, check=None, language=None,
               format=None, format_dict=None, format_mod=None, display=None,
               **kwargs):
        """Translate a line then log it."""

        language = pick(language, self.current)
        check = self.bypassed.get("check", pick(check, self.check))

        display = self.bypassed.get("display", pick(display, self.display))

        format = pick(format, ())
        format_dict = pick(format_dict, {})
        format_mod = pick(format_mod, ())

        output = self._get_output_list(output)

        if ("translate" not in self.bypassed and check and
                               language != self.main):

            trout = output[:]
            self.translate(trout, language, format, format_dict, format_mod)

            trfile = self.all_languages[language] + "_" + file

            super().logger(*trout, file=trfile, display=display, **kwargs)

            display = self.bypassed.get("display", False)

        if check:
            self.translate(output, self.main, format, format_dict, format_mod)

        super().logger(*output, file=file, display=display, **kwargs)

class TranslatedTypeLogger(Translater, TypeLogger):
    """Implement translated type-based logging."""

class LevelLogger(BaseLogger):
    """Implement levelled logging.

    "level":
                    Number specifying the default level at which lines
                    will be logged.

        Default:    0

    Bypassers arguments:

    "level":
                    Bypasser to override the "level" parameter given to
                    the logger method. The resulting value must be a
                    number or None.

    """

    def __init__(self, *, level=None, file=None, **kwargs):
        """Create a new levelled logging instance."""

        super().__init__(**kwargs)

        self.default_level = pick(level, 0)
        self.default_file = pick(file, "normal.log")

    @check_bypass
    def logger(self, *output, file=None, level=None, display=None, write=None,
               sep=None, split=None, use_utc=None, ts_format=None,
               print_ts=None, encoding=None, errors=None, **kwargs):
        """Log everything to screen and/or file. Always use this."""

        sep = pick(sep, self.separator)
        encoding = pick(encoding, self.encoding)
        errors = pick(errors, self.errors)
        split = self.bypassed.get("splitter", pick(split, self.split))
        display = self.bypassed.get("display", pick(display, self.display))
        write = self.bypassed.get("write", pick(write, self.write))

        timestamp = self._get_timestamp(use_utc, ts_format)
        # this is the file to write everything to
        logall = self.bypassed.get("logall")

        if display:
            self._print(*output, sep=sep, use_utc=use_utc, split=split,
                        ts_format=ts_format, print_ts=print_ts, errors=errors)
        if write:
            output = self._get_output(output, sep).splitlines()
            alines = [x for x in self.logfiles if x in
                                 self.bypassers("all")[0]]
            getter = [file]
            if logall:
                getter.append(logall)
            for log in getter:
                if (log == logall and type not in alines) or log is None:
                    continue
                atypes = "type.{0} - ".format(type) if log == logall else ""
                with open(log, "a", encoding=encoding, errors=errors) as f:
                    for writer in output:
                        f.write(timestamp + atypes + writer + "\n")

    def logger(self, *output, level=None, **kwargs):
        """Log a line based on level given."""

        level = self.bypassed.get("level", level)

        if level is not None and level >= self.level:
            super().logger(*output, **kwargs)

class TranslatedLevelLogger(Translater, LevelLogger):
    """Implement a way to have levelled logging with translating."""

class NamesLogger(LevelLogger):
    """Implement named levels logging.

    "levels":
                    Mapping of {name: level} pairs, which are used to
                    implement named logging. This supports mutation of
                    the mapping to update the internal mapping.

        Default:    {}

    To add, change or remove a level after instantiation, either the
    original mapping can be altered, or direct change can be made via
    `logger.levels[level_to_change] = new_value` or similar.

    Bypassers arguments:

    "level":
                    Used to override the "level" parameter given to the
                    logger method. The resulting value must be a lookup
                    to a value in the mapping, a number, a name
                    matching a level, or None.

    """

    def __init__(self, *, levels=None, default=None, **kwargs):
        """Create a new instance of the named levels logger."""

        super().__init__(**kwargs)

        self.default = pick(default, "normal")
        self.levels = pick(levels, {})

        if self.default not in self.levels:
            self.levels[self.default] = 0

    def logger(self, *output, level=None, **kwargs):
        """Log a line matching a named level."""

        level = self.levels.get(level)
        if level is None:
            level = self.default

        super().logger(*output, level=level, **kwargs)

class TranslatedNamesLogger(Translater, NamesLogger):
    """Implement a way to use named levels with translating."""
