from __future__ import with_statement
from ConfigParser import ConfigParser
import os.path
from StringIO import StringIO
import zipfile

from django.contrib.sites.models import Site
from django.core.files.base import ContentFile
from django import forms

from uploadtemplate import models

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

        if not zip_file.getinfo('meta.ini'):
            raise forms.ValidationError(
                'Uploaded theme is invalid: missing meta.ini file')

        return zip_file

    def save(self):
        if not self.is_valid():
            raise ValueError("Cannot save an invalid upload.")

        zip_file = self.cleaned_data['theme']

        meta_file = StringIO(zip_file.read('meta.ini'))

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
            theme.thumbnail.save(path,
                                 ContentFile(zip_file.read(path)))

        static_root = theme.static_root()
        template_dir = theme.template_dir()

        for filename in zip_file.namelist():
            dirname, basename = os.path.split(filename)
            output_path = None
            if dirname.startswith('static'):
                dirname = dirname[len('static/'):]
                os.makedirs(os.path.join(static_root, dirname))
                output_path = os.path.join(static_root, dirname,
                                           basename)
            elif dirname.startswith('templates'):
                dirname = dirname[len('templates/'):]
                os.makedirs(os.path.join(template_dir, dirname))
                output_path = os.path.join(template_dir, dirname, basename)

            if output_path is not None:
                with file(output_path, 'wb') as output_file:
                    output_file.write(zip_file.read(filename))

        return theme
