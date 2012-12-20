import re

from django.conf import settings


PROTECTED_RE_CACHE = {}


def _is_protected(name, setting):
    # The setting is expected to be a list of compiled regular
    # expressions or strings to be compiled.
    if setting not in PROTECTED_RE_CACHE:
        try:
            protected_names = getattr(settings, setting)
        except AttributeError:
            protected_names = []

        try:
            protected_names = list(protected_names)
        except TypeError:
            protected_names = []

        regexps = []
        for regexp in protected_names:
            if isinstance(regexp, basestring):
                try:
                    regexps.append(re.compile(regexp))
                except re.error:
                    pass
            else:
                regexps.append(regexp)

        PROTECTED_RE_CACHE[setting] = regexps

    for regexp in PROTECTED_RE_CACHE[setting][:]:
        try:
            protected = regexp.match(name)
        except (AttributeError, TypeError):
            PROTECTED_RE_CACHE[setting].remove(regexp)
        else:
            if protected:
                return True

    return False


def is_protected_template(name):
    return _is_protected(name, 'UPLOADTEMPLATE_PROTECTED_TEMPLATE_NAMES')


def is_protected_static_file(name):
    return _is_protected(name, 'UPLOADTEMPLATE_PROTECTED_STATIC_FILES')
