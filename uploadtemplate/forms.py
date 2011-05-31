from __future__ import with_statement
from ConfigParser import ConfigParser
import os.path
from StringIO import StringIO
import zipfile
import hashlib

from django.contrib.sites.models import Site
from django.core.files.base import ContentFile
from django import forms

from uploadtemplate import models

def _zip_prefix(zip_file):
    meta_files = [name for name in zip_file.namelist()
                      if os.path.split(name)[1] == 'meta.ini']
    if not meta_files:
        return None
    return os.path.split(meta_files[0])[0]

class ThemeUploadForm(forms.Form):

    theme = forms.FileField(label="Theme ZIP")

    def clean_theme(self):
        value = self.cleaned_data.get('theme')
        if not value:
            return value

        try:
            zip_file = zipfile.ZipFile(value)
        except zipfile.error:
            raise forms.ValidationError('Uploaded theme is not a ZIP file')

        if _zip_prefix(zip_file) is None:
            raise forms.ValidationError(
                'Uploaded theme is invalid: missing meta.ini file')

        return zip_file

    def save(self):
        if not self.is_valid():
            raise ValueError("Cannot save an invalid upload.")

        zip_file = self.cleaned_data['theme']

        prefix = _zip_prefix(zip_file)

        meta_file = StringIO(zip_file.read(
                os.path.join(prefix, 'meta.ini')))

        config = ConfigParser()
        config.readfp(meta_file, 'meta.ini')

        theme = models.Theme.objects.create_theme(
            site = Site.objects.get_current(),
            name = config.get('Theme', 'name'))

        if config.has_option('Theme', 'description'):
            theme.description = config.get('Theme', 'description')
            theme.save()

        if config.has_option('Theme', 'thumbnail'):
            path = config.get('Theme', 'thumbnail')
            name, ext = os.path.splitext(path)
            # Sometimes, thumbnail names get too long.
            # At that point, just shorten them a hash of their content,
            # plus the extension. We use a hash of their content here
            # to avoid accidentally overwriting other files just because
            # two files happen to share a name.
            thumbnail_filename = theme.name + ext
            thumbnail_content = zip_file.read(
                        os.path.join(prefix, path))

            if len(thumbnail_filename) >= theme.thumbnail.field.max_length:
                # Uh oh, the filename will be too long for us to store in
                # the database. In that case, let's use the hash of the
                # file content.
                digest = hashlib.sha1(thumbnail_content).hexdigest()
                thumbnail_filename = 'img-' + digest + ext
                assert (len(thumbnail_filename) <
                        theme.thumbnail.field.max_length)

            theme.thumbnail.save(thumbnail_filename,
                                 ContentFile(thumbnail_content))

        static_root = theme.static_root()
        template_dir = theme.template_dir()

        for filename in zip_file.namelist():
            if prefix and not filename.startswith(prefix):
                continue
            dirname, basename = os.path.split(filename)
            if prefix:
                dirname = dirname[len(prefix)+1:]
            output_path = None
            if dirname.startswith('static'):
                dirname = dirname[len('static/'):]
                if not os.path.exists(os.path.join(static_root, dirname)):
                    os.makedirs(os.path.join(static_root, dirname))
                output_path = os.path.join(static_root, dirname,
                                           basename)
            elif dirname.startswith('templates'):
                dirname = dirname[len('templates/'):]
                if not os.path.exists(os.path.join(template_dir, dirname)):
                    os.makedirs(os.path.join(template_dir, dirname))
                output_path = os.path.join(template_dir, dirname, basename)
            if output_path is not None and not os.path.exists(output_path):
                with file(output_path, 'wb') as output_file:
                    output_file.write(zip_file.read(filename))

        return theme
