import zipfile

from django.core.exceptions import ValidationError
import mock

from uploadtemplate.forms import ThemeForm
from uploadtemplate.models import Theme
from uploadtemplate.tests import BaseTestCase


class ThemeFormTestCase(BaseTestCase):
    def test_name_not_given(self):
        form = ThemeForm({'name': '',
                          'theme_files_zip': None})
        self.assertFalse(form.is_valid())

    def test_zip_not_given(self):
        form = ThemeForm({'name': 'theme',
                          'theme_files_zip': None})
        self.assertTrue(form.is_valid())
        self.assertTrue(form.cleaned_data['theme_files_zip'] is None)

    def test_clean_zip__invalid(self):
        form = ThemeForm()
        data_file = self._data_file('zips/invalid.zip')
        form.cleaned_data = {'theme_files_zip': data_file}
        self.assertRaisesMessage(ValidationError,
                                 'Must be a valid zip archive.',
                                 form.clean_theme_files_zip)
        data_file.close()

    def test_clean_zip__empty(self):
        form = ThemeForm()
        data_file = self._data_file('zips/empty.zip')
        form.cleaned_data = {'theme_files_zip': data_file}
        with zipfile.ZipFile(data_file, 'r') as zip_file:
            self.assertEqual(len(zip_file.namelist()), 0)
        self.assertRaisesMessage(ValidationError,
                                 'Zip archive cannot be empty.',
                                 form.clean_theme_files_zip)
        data_file.close()

    def test_clean_zip__evil_root(self):
        form = ThemeForm()
        data_file = self._data_file('zips/evil_root.zip')
        form.cleaned_data = {'theme_files_zip': data_file}
        with zipfile.ZipFile(data_file, 'r') as zip_file:
            namelist = zip_file.namelist()
            self.assertEqual(len(namelist), 1)
            self.assertTrue(namelist[0].startswith('/'))
        self.assertRaisesMessage(ValidationError,
                                 'Zip archive contains invalid names.',
                                 form.clean_theme_files_zip)
        data_file.close()

    def test_clean_zip__evil_relative(self):
        form = ThemeForm()
        data_file = self._data_file('zips/evil_relative.zip')
        form.cleaned_data = {'theme_files_zip': data_file}
        with zipfile.ZipFile(data_file, 'r') as zip_file:
            namelist = zip_file.namelist()
            self.assertEqual(len(namelist), 1)
            self.assertTrue('..' in namelist[0].split('/'))
        self.assertRaisesMessage(ValidationError,
                                 'Zip archive contains invalid names.',
                                 form.clean_theme_files_zip)
        data_file.close()

    def test_clean_zip__valid(self):
        form = ThemeForm()
        data_file = self._data_file('zips/theme.zip')
        form.cleaned_data = {'theme_files_zip': data_file}
        self.assertEqual(form.clean_theme_files_zip(), data_file)
        data_file.close()

    def test_save(self):
        data_file = self._data_file('zips/theme.zip')
        with mock.patch.object(Theme, 'save_files') as save_files:
            with mock.patch.object(Theme, 'prune_files') as prune_files:
                form = ThemeForm({'name': 'Theme',
                                  'theme_files_zip': data_file})
                self.assertTrue(form.is_valid())
                self.assertTrue(form.instance.site_id is None)
                form.save()
                save_files.assert_called_once_with()
                prune_files.assert_called_once_with()
                self.assertFalse(form.instance.site_id is None)
        data_file.close()
