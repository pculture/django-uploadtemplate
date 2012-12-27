import os

from django.contrib.sites.models import Site
from django.core.files import File
from django.test import TestCase

import uploadtemplate
from uploadtemplate.models import Theme


class BaseTestCase(TestCase):
    urls = 'uploadtemplate.urls'

    def _data_file_path(self, data_file):
        root = os.path.abspath(os.path.dirname(uploadtemplate.__file__))
        return os.path.join(root, 'tests', 'data', data_file)

    def _data_file(self, data_file):
        return open(self._data_file_path(data_file))

    def create_theme(self, name='Theme', site=None, theme_zip=None,
                     **kwargs):
        self.assertFalse('theme_files_zip' in kwargs)
        if site is None:
            site = Site.objects.get_current()
        theme = Theme.objects.create(name=name, site=site, **kwargs)
        if theme_zip is not None:
            with self._data_file(theme_zip) as f:
                theme.theme_files_zip = File(f)
                theme.save()
        return theme
