import os
import zipfile

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from uploadtemplate.models import Theme
from uploadtemplate.tests import BaseTestCase


class ThemeTestCase(BaseTestCase):
    def test_theme_files_dir__no_pk(self):
        theme = Theme()
        self.assertTrue(theme.pk is None)
        self.assertRaises(AttributeError, getattr, theme, 'theme_files_dir')

    def test_theme_files_dir(self):
        theme = Theme(pk=1)
        self.assertEqual(theme.theme_files_dir,
                         'uploadtemplate/themes/1/')

    def test_save_files__no_zip(self):
        theme = Theme()
        theme.save_files()

    def test_save_files(self):
        theme = self.create_theme(theme_zip='zips/theme.zip')
        file_list = ['static/logo.png', 'templates/uploadtemplate/index.html']
        zip_file = zipfile.ZipFile(theme.theme_files_zip, 'r')
        self.assertEqual(set([n for n in zip_file.namelist()
                              if not n.endswith('/')]),
                         set(file_list))
        zip_file.close()
        theme.delete_files()
        self.assertEqual(theme.list_files(), [])
        theme.save_files()
        self.assertEqual(set(theme.list_files()),
                         set([os.path.join(theme.theme_files_dir, name)
                              for name in file_list]))
        theme.delete_files()
        self.assertEqual(theme.list_files(), [])

    def test_prune_files(self):
        theme = self.create_theme(theme_zip='zips/theme.zip')
        file_list = ['static/logo.png', 'templates/uploadtemplate/index.html']
        file_list = [os.path.join(theme.theme_files_dir, name)
                     for name in file_list]
        theme.delete_files()
        theme.save_files()
        self.assertEqual(set(theme.list_files()), set(file_list))
        new_file = os.path.join(theme.theme_files_dir, 'static/other.png')
        default_storage.save(new_file, ContentFile(''))
        self.assertEqual(set(theme.list_files()), set(file_list + [new_file]))
        theme.prune_files()
        self.assertEqual(set(theme.list_files()), set(file_list))
