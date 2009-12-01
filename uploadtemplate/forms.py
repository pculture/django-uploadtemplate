from __future__ import with_statement
import os.path
import re

from django.conf import settings
from django import forms
from django.template import (loader, TemplateDoesNotExist, VARIABLE_TAG_START,
                             VARIABLE_TAG_END, BLOCK_TAG_START, BLOCK_TAG_END)

UPLOADTEMPLATE_MAX_SIZE = 64 * 2**10 # 64Kb

TAG_RE = re.compile(r'%s(.*?)%s|%s(.*?)%s' % (
        VARIABLE_TAG_START, VARIABLE_TAG_END, BLOCK_TAG_START, BLOCK_TAG_END))
SECURITY_RE = re.compile(r'settings[.](SECRET_KEY|ADMINS|MANAGERS|'
                         r'DATABASE_\w+|USTREAM_\w+|VIMEO_\w+|BITLY_\w+)')

class TemplateUploadForm(forms.Form):

    name = forms.CharField(label='Template Name')
    template = forms.FileField(label="Template")


    def clean_name(self):
        value = self.cleaned_data.get('name')
        if not value:
            return value

        try:
            loader.get_template(value)
        except TemplateDoesNotExist:
            raise forms.ValidationError('That name is not a valid template.')
        else:
            return value

    def clean_template(self):
        value = self.cleaned_data.get('template')
        if not value:
            return value

        if value.size > getattr(settings, 'UPLOADTEMPLATE_MAX_SIZE',
                                   UPLOADTEMPLATE_MAX_SIZE):
            raise forms.ValidationError('Uploaded template is too big.')
        return value

    def save(self):
        if not self.is_valid():
            raise ValueError("Cannot save an invalid upload.")

        data = self.cleaned_data['template'].read()
        start = 0
        match = TAG_RE.search(data)
        while match:
            for text in match.groups():
                if text is not None and SECURITY_RE.search(text):
                    data = data[:match.start()] + data[match.end():]
                    start = match.start()
                    break
            else:
                start = match.end()
            match = TAG_RE.search(data, start)

        path = os.path.join(
            settings.UPLOADTEMPLATE_MEDIA_ROOT,
            self.cleaned_data['name'])

        os.makedirs(os.path.dirname(path))

        with file(path, 'w') as template_file:
            template_file.write(data)
