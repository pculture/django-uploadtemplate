import os
import re
import zipfile

from django.conf import settings
from django.core.files.storage import default_storage


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


def is_zipfile(fp):
    """
    This is a version of zipfile.is_zipfile, adjusted to only work for file
    pointers, but to work in both python 2.6 and 2.7.

    """
    try:
        if zipfile._EndRecData(fp):
            return True         # file has correct magic number
    except IOError:
        pass
    return False


def list_files(root_dir):
    # Trying to list a dir that doesn't exist can cause errors.
    if not default_storage.exists(root_dir):
        return []
    directories, filenames = default_storage.listdir(root_dir)
    files = [os.path.join(root_dir, name) for name in filenames]
    for dirname in directories:
        files.extend(list_files(os.path.join(root_dir, dirname)))
    return files
