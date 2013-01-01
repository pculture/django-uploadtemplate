import os
import urlparse

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.template import Context, Variable
from django.test.utils import override_settings
import mock

from uploadtemplate.templatetags.uploadtemplate import static
from uploadtemplate.templatetags.uploadtemplate_tags import GetStaticUrlNode
from uploadtemplate.tests import BaseTestCase


class StaticTestCase(BaseTestCase):
    @override_settings(INSTALLED_APPS=())
    def test_static_url(self):
        self.create_theme(default=False)
        path = 'path/to/file.pth'
        with mock.patch('django.contrib.staticfiles.storage.staticfiles_storage') as storage:
            url = static(Context(), path)
            self.assertFalse(storage.url.called)
        self.assertEqual(url, urlparse.urljoin(settings.STATIC_URL, path))

    def test_staticfiles_url(self):
        self.create_theme(default=False)
        path = 'path/to/file.pth'
        context = Context()
        with mock.patch('django.contrib.staticfiles.storage.staticfiles_storage') as storage:
            static(context, path)
            storage.url.assert_called_once_with(path)

    def test_theme_url(self):
        theme = self.create_theme(default=True)
        path = 'path/to/file.pth'
        name = os.path.join(theme.theme_files_dir, 'static', path)
        if not default_storage.exists(name):
            default_storage.save(name, ContentFile(''))
        with mock.patch('uploadtemplate.templatetags.uploadtemplate.default_storage') as storage:
            static(Context(), path)
            storage.url.assert_called_once_with(name)

    def test_theme_url__nofile(self):
        self.create_theme(default=True)
        path = 'path/to/file.pth'
        with mock.patch('uploadtemplate.templatetags.uploadtemplate.default_storage') as storage:
            storage.exists.return_value = False
            static(Context(), path)
            self.assertFalse(storage.url.called)


class GetStaticUrlTestCase(BaseTestCase):
    def test_calls_static(self):
        path = 'path/to/file.pth'
        context = Context({'path': path})
        node = GetStaticUrlNode(Variable('path'))
        with mock.patch('uploadtemplate.templatetags.uploadtemplate_tags.static') as static:
            node.render(context)
            static.assert_called_once_with(context, path)
