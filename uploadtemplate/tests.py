import os.path
import shutil
from StringIO import StringIO
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from uploadtemplate import forms

class BaseTestCase(TestCase):

    urls = 'uploadtemplate.urls'
    template_name = 'uploadtemplate/test_template.html'

    def setUp(self):
        self.old_MEDIA_ROOT = settings.UPLOADTEMPLATE_MEDIA_ROOT
        self.old_TEMPLATE_LOADERS = settings.TEMPLATE_LOADERS
        self.old_TEMPLATE_DIRS = settings.TEMPLATE_DIRS
        self.old_CONTEXT_PROCESSORS = settings.TEMPLATE_CONTEXT_PROCESSORS

        self.tmpdir = tempfile.mkdtemp()
        settings.UPLOADTEMPLATE_MEDIA_ROOT = self.tmpdir
        settings.TEMPLATE_CONTEXT_PROCESSORS = []
        settings.TEMPLATE_LOADERS = [
            'django.template.loaders.filesystem.load_template_source']
        settings.TEMPLATE_DIRS = [
            os.path.join(os.path.dirname(__file__),
                         'test_templates')]

    def tearDown(self):
        settings.UPLOADTEMPLATE_MEDIA_ROOT = self.old_MEDIA_ROOT
        settings.TEMPLATE_LOADERS = self.old_TEMPLATE_LOADERS
        settings.TEMPLATE_DIRS = self.old_TEMPLATE_DIRS
        settings.TEMPLATE_CONTEXT_PROCESSORS = self.old_CONTEXT_PROCESSORS
        shutil.rmtree(self.tmpdir)

class TemplateUploadFormTestCase(BaseTestCase):
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


class ViewTestCase(BaseTestCase):

    def _create_template(self, content=''):
        """
        Create a fake template for testing.
        """
        os.makedirs(os.path.join(self.tmpdir, 'uploadtemplate'))
        f = file(os.path.join(self.tmpdir, self.template_name), 'w')
        f.write(content)
        f.close()

    def test_index_GET(self):
        """
        A GET request to the index view should render the
        'uploadtemplate/index.html' template, and include as the 'templates'
        variable the list of uploaded templates.
        """
        self._create_template()
        c = Client()
        response = c.get(reverse('uploadtemplate-index'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.template.name, 'uploadtemplate/index.html')
        self.assertEquals(response.context['templates'], [self.template_name])
        self.assertTrue(isinstance(response.context['form'],
                                   forms.TemplateUploadForm))

    def test_index_POST_invalid(self):
        """
        An invalid POST request to the index view should re-render the template
        and include the form with the errors.
        """
        c = Client()
        response = c.post(reverse('uploadtemplate-index'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.template.name, 'uploadtemplate/index.html')
        self.assertEquals(response.context['templates'], [])
        self.assertTrue(response.context['form'].is_bound)
        self.assertFalse(response.context['form'].is_valid())

    def test_index_POSY(self):
        """
        A valid POST request should save the uploaded template and redirect
        back to the index page.
        """
        f = StringIO('Template!')
        f.name = 'template.html' # Django's test client needs this attribute
        c = Client()
        response = c.post(reverse('uploadtemplate-index'),
                          {'name': self.template_name,
                          'template': f})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response['Location'],
                          'http://testserver%s' % (
                reverse('uploadtemplate-index')))
        self.assertEquals(file(os.path.join(
                    self.tmpdir, self.template_name)).read(),
                          'Template!')

    def test_access_GET(self):
        """
        A GET request to the access view should render the
        'uploadtemplate/access.html' template and have the text of the template
        in the context.
        """
        data = 'Template!'
        self._create_template(data)
        c = Client()
        response = c.get(reverse('uploadtemplate-access',
                                 args=[self.template_name]))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.template.name, 'uploadtemplate/access.html')
        self.assertEquals(response.context['template'], self.template_name)
        self.assertEquals(response.context['data'], data)

    def test_access_GET_raw(self):
        """
        A GET request to the access view with GET['format'] = 'raw' should just
        return the raw template data.
        """
        data = 'Template!'
        self._create_template(data)
        c = Client()
        response = c.get(reverse('uploadtemplate-access',
                                 args=[self.template_name]),
                         {'format': 'raw'})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, data)

    def test_access_GET_404(self):
        """
        If the template has not been uploaded, the page should be a 404.
        """
        c = Client()
        response = c.get(reverse('uploadtemplate-access',
                                 args=[self.template_name]))
        self.assertEquals(response.status_code, 404)

    def test_access_DELETE(self):
        """
        A DELETE request to the access view should delete the template and
        redirect back to the indes view.
        """
        data = 'Template!'
        self._create_template(data)
        c = Client()
        response = c.delete(reverse('uploadtemplate-access',
                                 args=[self.template_name]))
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response['Location'],
                          'http://testserver%s' % (
                reverse('uploadtemplate-index')))
        self.assertFalse(os.path.exists(
                os.path.join(self.tmpdir, self.template_name)))

    def test_access_DELETE_404(self):
        """
        If the template has not been uploaded, the page should be a 404.
        """
        c = Client()
        response = c.get(reverse('uploadtemplate-access',
                                 args=[self.template_name]))
        self.assertEquals(response.status_code, 404)
