from __future__ import with_statement
import os.path
import shutil
from StringIO import StringIO
import tempfile
import zipfile

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from uploadtemplate import forms
from uploadtemplate import models

class BaseTestCase(TestCase):

    urls = 'uploadtemplate.urls'
    _theme_zip = None

    def setUp(self):
        try:
            Site.objects.get_current()
        except Site.DoesNotExist:
            Site.objects.create(
                pk=settings.SITE_ID,
                domain='example.com',
                name='example')
        self.old_MEDIA_ROOT = settings.MEDIA_ROOT
        self.old_UPLOAD_MEDIA_ROOT = settings.UPLOADTEMPLATE_MEDIA_ROOT
        self.old_TEMPLATE_LOADERS = settings.TEMPLATE_LOADERS
        self.old_TEMPLATE_DIRS = settings.TEMPLATE_DIRS
        self.old_CONTEXT_PROCESSORS = settings.TEMPLATE_CONTEXT_PROCESSORS

        self.tmpdir = tempfile.mkdtemp()
        settings.UPLOADTEMPLATE_MEDIA_ROOT = settings.MEDIA_ROOT = self.tmpdir
        settings.TEMPLATE_CONTEXT_PROCESSORS = []
        settings.TEMPLATE_LOADERS = [
            #'uploadtemplate.loader.load_template_source',
            'django.template.loaders.filesystem.load_template_source']
        settings.TEMPLATE_DIRS = [
            os.path.join(os.path.dirname(__file__), 'testdata', 'templates')]

    def tearDown(self):
        settings.UPLOADTEMPLATE_MEDIA_ROOT = self.old_UPLOAD_MEDIA_ROOT
        settings.MEDIA_ROOT = self.old_MEDIA_ROOT
        settings.TEMPLATE_LOADERS = self.old_TEMPLATE_LOADERS
        settings.TEMPLATE_DIRS = self.old_TEMPLATE_DIRS
        settings.TEMPLATE_CONTEXT_PROCESSORS = self.old_CONTEXT_PROCESSORS
        shutil.rmtree(self.tmpdir)

    def theme_zip(self):
        """
        Generate/return a ZIP file of the test theme.
        """
        if not self._theme_zip:
            self._theme_zip = StringIO()
            zip = zipfile.ZipFile(self._theme_zip, 'w')
            root = os.path.join(os.path.dirname(__file__),
                                'testdata', 'theme')
            for dirname, dirs, files in os.walk(root):
                for filename in files:
                    full_path = os.path.join(dirname, filename)
                    with file(full_path, 'rb') as f:
                        zip.writestr(full_path[len(root)+1:],
                                        f.read())
            zip.close()
        self._theme_zip.seek(0)
        return self._theme_zip

class ThemeUploadFormTestCase(BaseTestCase):
    def test_theme_required(self):
        """
        The uploaded theme is required.
        """
        form = forms.ThemeUploadForm()
        self.assertFalse(form.is_valid())

    def test_zip_required(self):
        """
        The uploaded theme must be a ZIP file.
        """
        form = forms.ThemeUploadForm({},
            {'theme': SimpleUploadedFile('theme.zip',
                                         'Not a ZIP file!')})
        self.assertFalse(form.is_valid())

    def test_meta_ini_required(self):
        """
        The uploaded theme must have a meta.ini file.
        """
        si = StringIO()
        zip = zipfile.ZipFile(si, 'w')
        zip.close()
        si.seek(0)

        form = forms.ThemeUploadForm({},
            {'theme': SimpleUploadedFile('theme.zip',
                                         si.read())})
        self.assertFalse(form.is_valid())

    def test_upload(self):
        """
        ThemeUploadForm().save() should write the given theme to
        settings.UPLOADTEMPLATE_MEDIA_ROOT and create a Theme object..
        """
        form = forms.ThemeUploadForm({},
            {'theme': SimpleUploadedFile('theme.zip',
                                         self.theme_zip().read())})
        self.assertTrue(form.is_valid(), form.errors)

        theme = form.save()
        self.assertTrue(theme.default)
        self.assertEquals(theme.name, 'UploadTemplate Test Theme')
        self.assertEquals(theme.thumbnail.name,
                          'uploadtemplate/theme_thumbnails/thumbnail.gif')
        self.assertTrue(theme.static_root().startswith(
                settings.UPLOADTEMPLATE_MEDIA_ROOT))
        self.assertTrue(theme.template_dir().startswith(
                settings.UPLOADTEMPLATE_MEDIA_ROOT))
        self.assertTrue(os.path.exists(os.path.join(theme.static_root(),
                                                    'logo.png')))
        self.assertTrue(os.path.exists(os.path.join(theme.template_dir(),
                                                    'index.html')))

class ViewTestCase(BaseTestCase):

    def setUp(self):
        BaseTestCase.setUp(self)
        form = forms.ThemeUploadForm(
            {},
            {'theme': SimpleUploadedFile('theme.zip',
                                         self.theme_zip().read())})
        self.theme = form.save()

    def test_index_GET(self):
        """
        A GET request to the index view should render the
        'uploadtemplate/index.html' template, and include as the 'templates'
        variable the list of uploaded templates.
        """
        c = Client()
        response = c.get(reverse('uploadtemplate-index'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.template.name, 'uploadtemplate/index.html')
        self.assertEquals(response.context['default'], self.theme)
        self.assertEquals(list(response.context['themes']),
                          [self.theme])
        self.assertEquals(list(response.context['non_default_themes']), [])
        self.assertTrue(isinstance(response.context['form'],
                                   forms.ThemeUploadForm))

    def test_index_POST_invalid(self):
        """
        An invalid POST request to the index view should re-render the template
        and include the form with the errors.
        """
        c = Client()
        response = c.post(reverse('uploadtemplate-index'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.template.name, 'uploadtemplate/index.html')
        self.assertEquals(response.context['default'], self.theme)
        self.assertTrue(response.context['form'].is_bound)
        self.assertFalse(response.context['form'].is_valid())

    def test_index_POST(self):
        """
        A valid POST request should save the uploaded theme and redirect
        back to the index page.
        """
        self.theme.name = 'Old Theme'
        self.theme.save()

        f = self.theme_zip()
        f.name = 'theme.zip'

        c = Client()
        response = c.post(reverse('uploadtemplate-index'),
                          {'theme': f})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response['Location'],
                          'http://testserver%s' % (
                reverse('uploadtemplate-index')))

        self.assertEquals(models.Theme.objects.count(), 2)
        self.assertEquals(models.Theme.objects.get_default().pk, 2)


    def test_set_default(self):
        """
        A request to the set_default view should change the default theme.
        """
        self.theme.name = 'Old Theme'
        self.theme.save()

        form = forms.ThemeUploadForm(
            {}, {'theme': SimpleUploadedFile('theme.zip',
                                             self.theme_zip().read())})
        form.save()

        c = Client()
        response = c.get(self.theme.get_absolute_url())
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response['Location'],
                          'http://testserver%s' % (
                reverse('uploadtemplate-index')))

        theme = models.Theme.objects.get_default()
        self.assertEquals(theme, self.theme)
