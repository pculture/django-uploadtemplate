import os.path
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from uploadtemplate import forms

class TemplateUploadTestCase(TestCase):

    template_name = 'uploadtemplate/test_template.html'

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.old_MEDIA_ROOT = settings.UPLOADTEMPLATE_MEDIA_ROOT
        settings.UPLOADTEMPLATE_MEDIA_ROOT = self.tmpdir

    def tearDown(self):
        settings.UPLOADTEMPLATE_MEDIA_ROOT = self.old_MEDIA_ROOT
        shutil.rmtree(self.tmpdir)

    def test_name_required(self):
        """
        The name of the template is required.
        """
        form = forms.TemplateUploadForm(
            {},
            {'template': SimpleUploadedFile('template.html',
                                            '')})
        self.assertFalse(form.is_valid())

    def test_name_must_exist(self):
        """
        The name of the template must be an already existing template.
        """
        form = forms.TemplateUploadForm(
            {'name': 'uploadtemplate/invalid_template.html'},
            {'template': SimpleUploadedFile('template.html',
                                            '')})
        self.assertFalse(form.is_valid())

    def test_template_required(self):
        """
        The uploaded template is required.
        """
        form = forms.TemplateUploadForm(
            {'name': self.template_name})
        self.assertFalse(form.is_valid())

    def test_upload(self):
        """
        TemplateUploadForm().save() should write the given template to
        settings.UPLOADTEMPLATE_MEDIA_ROOT.
        """
        form = forms.TemplateUploadForm(
            {'name': self.template_name},
            {'template': SimpleUploadedFile('template.html',
                                            'Template!')})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEquals(file(os.path.join(
                    self.tmpdir, self.template_name)).read(),
                          'Template!')

    def test_security_variable(self):
        """
        If the uploaded template uses a variable that's security related (like
        SECRET_KEY), that variable tag should be stripped from the saved
        template.
        """
        form = forms.TemplateUploadForm(
            {'name': self.template_name},
            {'template': SimpleUploadedFile('template.html',
                                            '-{{ settings.SECRET_KEY }}-')})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEquals(file(os.path.join(
                    self.tmpdir, self.template_name)).read(),
                          '--')

    def test_security_block(self):
        """
        If the uploaded template uses a block tag that includes a variable
        that's security related, that block tag should be stripped from the
        saved template.
        """
        form = forms.TemplateUploadForm(
            {'name': self.template_name},
            {'template': SimpleUploadedFile(
                    'template.html',
                    '-{% for settings.SECRET_KEY %}-')})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEquals(file(os.path.join(
                    self.tmpdir, self.template_name)).read(),
                          '--')

    def test_variable(self):
        """
        Non-security veriables should be passed through unchanged.
        """
        form = forms.TemplateUploadForm(
            {'name': self.template_name},
            {'template': SimpleUploadedFile(
                    'template.html',
                    '-{{ settings.MEDIA_ROOT }}-')})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEquals(file(os.path.join(
                    self.tmpdir, self.template_name)).read(),
                          '-{{ settings.MEDIA_ROOT }}-')

    def test_block(self):
        """
        Non-security blocks should be passed through unchanged.
        """
        form = forms.TemplateUploadForm(
            {'name': self.template_name},
            {'template': SimpleUploadedFile(
                    'template.html',
                    '-{% for settings.MEDIA_ROOT %}-')})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEquals(file(os.path.join(
                    self.tmpdir, self.template_name)).read(),
                          '-{% for settings.MEDIA_ROOT %}-')
