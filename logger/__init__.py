#!/usr/bin/env python

__author__ = "Emanuel 'Vgr' Barry"

__version__ = "0.2.2"
__status__ = "Refactoring [Unstable]"

__all__ = ["TypeLogger", "TranslatedTypeLogger",        # type-based loggers
           "LevelLogger", "TranslatedLevelLogger",      # level-based loggers
           "NamesLogger", "TranslatedNamesLogger",      # names-based loggers
           "log_usage", "log_use", "check_definition",  # decorators
           "chk_def", "NoValue"]

import shutil
import sys
import re

from logger import bypassers

import _novalue as NoValue

def pick(arg, default):
    """Handler for default versus given argument."""
    return default if arg is None else arg

def handle_bypass(func):
    """Default bypasser handler for methods that do not support it."""
    def inner(self, *args, **kwargs):
        if not hasattr(self, "bypassed"):
            self.bypassed = {}
            try:
                return func(self, *args, **kwargs)
            finally:
                del self.bypassed
        return func(self, *args, **kwargs)
    return inner

def check_bypass(func):
    """Handler to get the proper bypass check decorator."""
    def inner(self, *output, **kwargs):
        self.bypassed = {}
        name = "check_bypass_" + self._bp_handler
        try:
            return getattr(bypassers, name)(func, self, *output, **kwargs)
        finally:
            del self.bypassed

    return inner

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
                    uppercased.. The time zone offset is a string with
                    + or - following by 4 digits, like +0000 or -0500,
                    the digits being HHMM.

        Default:    "[%Y-%m-%-d] (%H:%M:%S {tzoffset})"

    print_ts:
                    Boolean value to determine whether the timestamps
                    should be printed to screen as well as to files.

        Default:    False

    split:
                    Boolean value to determine if long lines should be
                    split when printing to screen.

        Default:    True

    """

    _bp_handler = "base"

    def __init__(self, *, sep=None, use_utc=None, ts_format=None,
                       print_ts=None, split=None, bypassers=None, **kwargs):
        """Create a new base instance."""

        super().__init__(**kwargs)

        self.separator = pick(sep, " ")

        self.use_utc = pick(use_utc, False)
        self.print_ts = pick(print_ts, False)
        self.split = pick(split, True)

        # this needs to be list/tuple of (setting, types, pairs,
        # module, attr) tuples; the setting is the setting to bypass;
        # types is a list of types to check for to determine if
        # bypassing should occur, same about the pairs, except for
        # module/attr matches; module and attr are used with getattr()
        # to bypass the value of setting with the one found in the
        # given module, for the given attribute; module of None means
        # to use the attr as the direct value; making the type None
        # will also indicate that any type can be triggered. To
        # indicate a lack of value for any parameter, pass NoValue, as
        # None has a special meaning

        func = getattr(globals()["bypassers"], self._bp_handler.capitalize() +
                                               "Bypassers")

        self.bypassers = func(*pick(bypassers, ()))
        self.bypassers.add("timestamp", "splitter")

        # this can have {tzname} and {tzoffset} for formatting
        # this adds respectively a timezone in the format UTC or EST
        # and an offset from UTC in the form +0000 or -0500
        self.ts_format = pick(ts_format, "[%Y-%m-%d] (%H:%M:%S {tzoffset})")

    def __dir__(self):
        """Return a list of all non-private methods and attributes."""
        items = set(dir(self.__class__) + list(self.__dict__))
        for item in set(items):
            if item[0] == "_" and not bypassers.is_dunder(item):
                items.remove(item)
        return items

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
        return tmf.format(tzname=tz, tzoffset=offset).strip().upper() + " "

    def _split_lines(self, out):
        """Split long lines at clever points."""
        col = shutil.get_terminal_size()[0]
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
                              print_ts=None, split=None):
        """Print to screen and remove all invalid characters."""

        sep = pick(sep, self.separator)

        output = self._get_output(output, sep)

        if pick(print_ts, self.print_ts):
            out = output.splitlines()
            ts = self._get_timestamp(use_utc, ts_format)
            for i, line in enumerate(out):
                out[i] = ts + line
            output = "\n".join(out)

        if self.bypassed.get("splitter", pick(split, self.split)):
            output = self._split_lines(output)

        with open(sys.stdout.fileno(), "w", errors="replace",
                  encoding="utf-8", closefd=False) as file:

            file.write(output + "\n")

            file.flush()

    def _get_output(self, out, sep, ret_list=False):
        """Sanitize output and join iterables together."""
        out = out or [''] # called with no argument, support it anyway
        msg = [] if ret_list else None
        for line in out:
            line = str(line)
            if msg is None:
                msg = line
            elif ret_list:
                msg.append(line)
            else:
                msg = sep.join((msg, line))
        return msg

    def logger(self, *output, sep=None, file=None, split=None,
               use_utc=None, ts_format=None, print_ts=None):
        """Base method to make sure it always exists."""
        output = self._get_output(output, pick(sep, self.separator))
        self._print(output, sep=sep, use_utc=use_utc, ts_format=ts_format,
                            print_ts=print_ts, split=split)
        if file is not None:
            with open(file, "a") as f:
                f.write(output + "\n")

class TypeLogger(BaseLogger):
    """Main Logger class for general and specific logging purposes.

    This is inherited from the BaseLogger class.

    The options are the same as the base class, with these additions:

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

    logfiles:
                    Dictionary of {type:file} pairs. The type is the
                    logging type that the logger expects. The file is
                    the file that tells the logger to write to. This
                    can be used for dynamic file logging.

        Default:    {"normal": "logger.log", "all": "mixed.log"}

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

    _bp_handler = "type"

    def __init__(self, *, write=None, display=None, logfiles=None, **kwargs):
        """Create a new type-based logger."""

        super().__init__(**kwargs)

        self.display = pick(display, True)
        self.write = pick(write, True)

        files = {"normal": "logger.log"}

        if logfiles is not None:
            self.logfiles = logfiles
            for type, file in files.items():
                # if the type is already defined, don't overwrite it
                # only add to it if it doesn't exist
                self.logfiles[type] = self.logfiles.get(type, file)
        else:
            self.logfiles = files

        self.bypassers.add("display", "write", "logall", "files", "all")

    @check_bypass
    def logger(self, *output, file=None, type=None, display=None, write=None,
               sep=None, split=None, use_utc=None, ts_format=None,
               print_ts=None):
        """Log everything to screen and/or file. Always use this."""

        sep = pick(sep, self.separator)
        split = self.bypassed.get("splitter", pick(split, self.split))
        display = self.bypassed.get("display", pick(display, self.display))
        write = self.bypassed.get("write", pick(write, self.write))

        timestamp = self._get_timestamp(use_utc, ts_format)
        # this is the file to write everything to
        logall = self.bypassed.get("logall")

        if display:
            self._print(*output, sep=sep, use_utc=use_utc, split=split,
                         ts_format=ts_format, print_ts=print_ts)
        if write:
            output = self._get_output(output, sep).splitlines()
            alines = [x for x in self.logfiles if x in
                                 self.bypassers["all"][0]]
            getter = [file]
            if logall:
                getter.append(logall)
            for log in getter:
                if (log == logall and type not in alines) or log is None:
                    continue
                atypes = "type.%s - " % type if log == logall else ""
                with open(log, "a", encoding="utf-8", errors="replace") as f:
                    for writer in output:
                        f.write(timestamp + atypes + writer + "\n")

    def multiple(self, *output, types=None, display=None, **rest):
        """Log one or more line to multiple files."""
        types = pick(types, ["normal"])

        if len(types) == 1 and "*" in types: # allows any iterable
            for log in self.logfiles:
                if log not in self.bypassers["files"][0]:
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

class Translater:
    """Logging class to use to translate lines.

    This is inherited from the BaseLogger class.
    This needs to be used in multiple inheritence to work properly.
    The parameters are the same as for the base class, plus these:

    main:
                    The main language that will be used. This is
                    considered the "default" language, and is the one
                    that will be used to write to the normal files. It
                    will always be written to the files, no matter what
                    language is being used.

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

        Default:    "[A-Z0-9_]*" - UPPERCASE_UNDERSCORED_NAMES

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

    - It requires an iterable of strings to be passed in. Passing a single
      string will not work as intended.

    """

    def __init__(self, *, main=None, module=None, modules=None, first=None,
                 pattern=None, **kwargs):
        """Create a new translater object."""

        super().__init__(**kwargs)

        self.main = pick(main, "English")

        self.module = module
        self.modules = modules

        self.first = pick(first, "language")
        self.pattern = pick(pattern, "[A-Z0-9_]*")

    def translate(self, output, language, format, format_dict, format_mod):
        """Translate a line into the desired language."""

        def copy(name, new):
            return getattr(name.__class__, "copy", new)(name)

        format = copy(format, list)
        format_dict = copy(format_dict, dict)
        format_mod = copy(format_mod, list)

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
                if re.fullmatch(self.pattern, line) is None:
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
                    line = line.format(*format, **format_dict) % format_mod

                iterable[i] = line

class TranslatedTypeLogger(Translater, TypeLogger):
    """Implement translated type-based logging.

    This is used to implement translated type-based logging.
    The parameters are the same as the Translater and the Logger,
    with the following additions:

    all_languages:
                    Dictionary of {language:short} pairs. The language
                    is used for the standard lookup of the language.
                    The value is the 2-characters abbreviation of the
                    language. The default value is "English" for the
                    key, and "en" for the value. This must contain all
                    languages that this class will be asked to
                    translate to, see below for restrictions.

        Default:    {"English": "en"}

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

    check:
                    Boolean value that will determine if a line should
                    be checked for translation or not. If False, the
                    line will not be checked and will be printed or
                    writen to the file as-is

        Default:    True
    """

    def __init__(self, *, all_languages=None, current=None, check=None,
                       **kwargs):
        """Create a new instance of type-based translated logging."""

        super().__init__(**kwargs)

        langs = {"English": "en"}

        if all_languages is not None:
            self.all_languages = all_languages
            for long, short in langs.items():
                self.all_languages[long] = self.all_languages.get(long, short)
        else:
            self.all_languages = langs

        self.current = pick(current, self.main)
        self.check = pick(check, True)

        self.bypassers.update(("translate", set(), [], None, True))
        self.bypassers.add("check")

    @check_bypass
    def logger(self, *output, file=None, type=None, sep=None, check=None,
               language=None, format=None, format_dict=None, format_mod=None,
               **kwargs):
        """Log a line after translating it."""

        sep = pick(sep, self.separator)

        language = pick(language, self.current)
        check = self.bypassed.get("check", pick(check, self.check))

        format = pick(format, ())
        format_dict = pick(format_dict, {})
        format_mod = pick(format_mod, ())

        output = self._get_output(output, sep, True)

        if ("translate" not in self.bypassed and check and
                               language != self.main):
            trout = output[:]
            self.translate(trout, language, format, format_dict, format_mod)

            trfile = self.all_languages[language] + "_" + file

            super().logger(*trout, file=trfile, type=type, sep=sep, **kwargs)

            display = False

        if check:
            self.translate(output, self.main, format, format_dict, format_mod)

        super().logger(*output, file=file, type=type, sep=sep, **kwargs)

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

    _bp_handler = "level"

    def __init__(self, *, level=None, file=None, **kwargs):
        """Create a new levelled logging instance."""

        super().__init__(**kwargs)

        self.default_level = pick(level, 0)
        self.default_file = pick(file, "normal.log")

    def logger(self, *output, level=None, **kwargs):
        """Log a line based on level given."""

        level = self.bypassed.get("level", level)

        if level is not None and level >= self.level:
            super().logger(*output, **kwargs)

class TranslatedLevelLogger(Translater, LevelLogger):
    """Implement a way to have levelled logging with translating."""

class LoggingLevels(sys.__class__):
    """Module class for logging levels."""

    def __init__(self, *mappings, **items):
        """Create a new items mapping."""
        super().__init__(self.__class__.__name__, self.__class__.__doc__)
        for mapping in mappings:
            for level, value in mapping.items():
                setattr(self, level, value)

        for level, value in items.items():
            setattr(self, level, value)

    def __iter__(self):
        """Iterate over the items of self."""
        return (x for x in self.__dict__ if not bypassers.is_dunder(x))

    def __reversed__(self):
        """Iterate over the items by value instead of key."""
        return (self.__dict__[item] for item in self)

    @property
    def __reversed_lookup__(self):
        """Return a swapped dictionary."""
        return {self.__dict__[item]: item for item in self}

class NamesLogger(LevelLogger):
    """Implement named levels logging.

    "levels":
                    Mapping of {name:level} pairs, which are used to
                    implement named logging. This supports mutation of
                    the mapping to update the internal mapping.

        Default:    {}

    To add, change or remove a level after instantiation, either the
    original mapping can be altered, or direct change can be made via
    `self.levels.level_to_change = new_value` or similar.

    Passing the level value can be done either through a direct lookup
    with the `levels` argument, a number, a name matching a level, or
    None.

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
        self.levels = LoggingLevels(**pick(levels, {}))

        if self.default not in self.levels:
            setattr(self.levels, self.default, 0)

    def logger(self, *output, level=None, **kwargs):
        """Log a line matching a named level."""

        try: # string - direct value lookup (eg "info" is levels.info)
            level = getattr(self.levels, level)
        except TypeError: # got an int, direct value lookup, or None
            pass
        except AttributeError: # unknown value; fall back to normal
            level = getattr(self.levels, self.default)

        super().logger(*output, level=level, **kwargs)

class TranslatedNamesLogger(Translater, NamesLogger):
    """Implement a way to use named levels with translating."""

class log_usage:
    """Decorator to log function and method usage.

    There are three ways to use this decorator:

    >>> from logger import log_usage
    >>> @log_usage() # @log_usage(None) has the same effect
    ... def foo():
    ...     print("spam")
    ...
    >>> foo()
    Call: __main__.foo()
    spam

    >>> from logger import log_usage, Logger
    >>> handler = Logger()
    >>> @log_usage(handler)
    ... def foo(first, second, third=3, fourth=None):
    ...     print("eggs")
    ...
    >>> foo("bar", 42, 7, fourth=24)
    Call: __main__.foo('bar', 42, 7, fourth=24)
    eggs

    >>> from logger import log_usage, Logger
    >>> handler = Logger()
    >>> args = (42, 1337)
    >>> kwargs = {"foo": 0, "bar": 1}
    >>> def baz(hello, world, foo=7, bar=22):
    ...     print("spam or eggs")
    ...
    >>> log_usage.call(baz, handler, args, kwargs)
    Call: __main__.baz(42, 1337, foo=0, bar=1)
    spam or eggs

    The handler is the logger object that will be used for logging of
    the function and method usage.

    The `call` method is called when this class is used as a decorator,
    and can be called directly as well.

    The following are possible handlers; they are stated by priority
    (so the first handle takes precedence over the second, which takes
    precedence over the third, and so on).

    - A subclass of BaseLogger; an instance of it will be created and
      its 'logger' method will be used.
    - Any instance of BaseLogger or its subclasses; its 'logger' method
      will be used.
    - Any class, they will be instantiated and called directly.
    - Any function or method, they will be called directly.
    - Any instance of any class, they will be called directly.
    - None (or no passed function), BaseLogger's logger will be used

    If none of the above matches for some reason, it will create a new
    instance of BaseLogger and use its 'logger' method.

    It is very easy to subclass this into a decorator that doesn't
    require any parameter. See log_use for an example.

    The class attribute `_default_handler` is a BaseLogger subclass,
    or any class, but it must have a `logger` method.

    """

    _default_handler = BaseLogger

    def __init__(self, func=None):
        """Prepare the decorator."""
        funcion = tuple(type(fn) for fn in (pick, self.__init__, len))

        if func is None:
            self.handler = self._default_handler().logger
        elif isinstance(func, type) and issubclass(func, base):
            self.handler = func().logger
        elif isinstance(func, base):
            self.handler = func.logger
        elif isinstance(func, type):
            self.handler = func()
        elif isinstance(func, function) or isinstance(func.__class__, type):
            self.handler = func
        else:
            self.handler = self._default_handler().logger

    def __call__(self, func):
        """Call the handler."""
        return lambda *args, **rest: self.call(func, args, rest, self.handler)

    @classmethod
    def call(cls, func, args, kwargs, handler=None):
        """Log usage of a function or method and call it."""

        if handler is None:
            handler = cls._default_handler().logger

        if handler is func:
            raise RuntimeError("cannot decorate the function with itself")

        params = (", ".join(repr(x) for x in args),
                  ", ".join("%s=%r" % (k,v) for k,v in kwargs.items()))

        if all(params):
            params = ", ".join(params)
        else:
            params = "".join(params)

        # regex pattern for translation: r"^Call: .+\..+\(.*\)$"
        handler("Call: %s.%s(%s)" % (func.__module__, func.__name__, params))

        return func(*args, **kwargs)

class log_use(log_usage):
    """Usage logging decorator that doesn't require a handler.

    This can be easily subclassed to change the handler used, or simply
    change the handler at runtime.

    """

    def __init__(self, func):
        """Prepare a handler-less decorator."""
        self.handler = self._default_handler().logger
        self.func = func

    def __call__(self, *args, **kwargs):
        """Handle the calling of the function itself."""
        return self.call(self.func, args, kwargs, self.handler)

class check_definition:
    """Class to check functions and methods definitions.

    This can yield the definitions of functions and methods, and will
    recursively iterate through classes. It can accept any number of
    arguments, consisting of functions, methods, classes, modules, or
    any combination of those.

    """

    _default_handler = BaseLogger

    def __init__(self, *func, handler=None):
        """Parse the functions and methods."""
        if handler is None:
            handler = self._default_handler().logger
        self.parse(*func, handler=handler)

    @classmethod
    def parse(cls, *olds, handler=None, parser=None, msg=[], func=[]):
        """Parse the function definition. This is recursive."""

        flags = { # built from the dis module
        0x01: "OPTIMIZED",
        0x02: "NEWLOCALS",
        0x04: "VARARGS",
        0x08: "VARKEYWORDS",
        0x10: "NESTED",
        0x20: "GENERATOR",
        0x40: "NOFREE",
        }

        for runner in olds:

            name = getattr(runner, "__module__",
                   getattr(runner, "__name__", None))

            if name == "builtins":
                continue

            if name in sys.modules:
                mod = sys.modules[name]
            elif parser:
                mod = runner.__class__
            else:
                mod = runner

            if hasattr(mod, "__file__"):
                msg.append("Reading file %r" % mod.__file__)
            elif parser:
                msg.append("Reading class " + mod.__name__)
            else:
                msg.append("Reading module %r" % mod.__name__)

            mod = mod.__name__ # keep the string for later

            if isinstance(runner, type(NoValue.__new__)):
                fn = runner.__func__
                c = runner.__self__.__class__
                name = fn.__name__
                func.append(((mod, c, name), "Method %r of class " + c, fn))
                msg.append("Parsing method %r" % name)

            elif isinstance(runner, type):
                msg.append("Parsing class " + runner.__name__)
                cls.parse(*runner.__dict__.values(), parser=runner)

            # prevent recursive calls for modules, as that would lead
            # to an infinite (or arbitrarily long and memory-eating)
            # loop that could iterate over half of the standard library
            # modules... so, yeah, don't let that happen
            elif isinstance(runner, sys.__class__) and not parser:
                msg.append("Parsing module %r" % runner.__name__)
                cls.parse(*runner.__dict__.values(), parser=runner)

            elif hasattr(runner, "__code__"):
                name = runner.__name__
                if parser:
                    func.append(((mod, parser.__name__, name),
                         "Method %r of class " + parser.__name__, runner))
                    msg.append("Parsing method %r" % name)
                else:
                    func.append(((mod, name), "Function %r", runner))
                    msg.append("Parsing function %r" % name)

        for path, name, function in func:

            if hasattr(function, "__code__"):

                code = function.__code__

                attrs = []

                flag = 64
                co_flags = code.co_flags

                while co_flags and flag:
                    if co_flags >= flag:
                        attrs.append(flags[flag])
                        co_flags -= flag
                    flag >>= 1

                fname = code.co_name
                lineno = code.co_firstlineno

                defargs = pick(function.__defaults__, ())
                kwdefargs = pick(function.__kwdefaults__, {})

                msg.append("\n%s at line %r" % ((name % fname), lineno))
                string = "Definition: %s(" % ".".join(path)

                num = code.co_argcount + code.co_kwonlyargcount

                total = num + ("VARARGS" in attrs) + ("VARKEYWORDS" in attrs)

                args_pos = kwargs_pos = 0

                if "VARKEYWORDS" in attrs:
                    kwargs_pos = num + ("VARARGS" in attrs)

                if "VARARGS" in attrs:
                    args_pos = num

                elif code.co_kwonlyargcount:
                    args_pos = None

                if args_pos:
                    args_all = code.co_varnames[args_pos]

                elif args_pos is None:
                    args_all = ""

                else:
                    args_all = None

                if kwargs_pos:
                    kwargs_all = code.co_varnames[kwargs_pos]

                else:
                    kwargs_all = None

                varnames = code.co_varnames[:total]

                defaults = len(defargs) + len(kwdefargs)

                if code.co_argcount:
                    string += ", ".join(varnames[:-defaults])

                    if num != defaults and varnames[:-defaults]:
                        string += ", "

                if defargs:
                    named_pos = code.co_argcount - len(defargs)
                    union_vars = varnames[named_pos:code.co_argcount]
                    union = [[v] for v in union_vars]
                    union = [union[i] + [v] for i, v in enumerate(defargs)]
                    string += ", ".join("%s=%r" % (arg,v) for arg, v in union)

                    if kwdefargs or args_all or kwargs_all:
                        string += ", "

                if args_all is not None:
                    string += "*%s" % args_all

                    if kwdefargs or kwargs_all:
                        string += ", "

                if kwdefargs:
                    string += ", ".join("%s=%r" % i for i in kwdefargs.items())

                    if kwargs_all:
                        string += ", "

                if kwargs_all:
                    string += "**%s" % kwargs_all

                string += ")"

                msg.append(string)

        if handler is not None:
            handler("\n".join(msg))

        if parser is None:
            msg.clear()
            func.clear()
