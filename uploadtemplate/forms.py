import os
from StringIO import StringIO
import zipfile

from django.contrib.sites.models import Site
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django import forms

from uploadtemplate.models import Theme


class ThemeForm(forms.ModelForm):
    class Meta:
        model = Theme
        exclude = ('site',)

    def clean_theme_files_zip(self):
        value = self.cleaned_data.get('theme_files_zip')
        if not value:
            return value

        try:
            zip_file = zipfile.ZipFile(value)
        except zipfile.error:
            raise forms.ValidationError('Must be a valid zip archive.')

        names = zip_file.namelist()
        if not names:
            raise forms.ValidationError('Zip archive cannot be empty.')

        root_dirs = set()
        for n in names:
            if n.startswith('/') or '..' in n.split('/'):
                raise forms.ValidationError('Zip archive contains invalid names.')

            if '/' not in n:
                raise forms.ValidationError('Zip archive cannot contain files in its root.')

            root_dirs.add(n.split('/', 1)[0])

        if len(root_dirs) > 1:
            raise forms.ValidationError('Zip archive must contain a single directory at its root.')

        self._zip_file = zip_file
        self._zip_file_root = list(root_dirs)[0]

        return value

    def save(self, commit=True):
        if not self.is_valid():
            raise ValueError("Cannot save an invalid upload.")

        self.instance.site = Site.objects.get_current()
        instance = super(ThemeForm, self).save(commit=False)

        old_save_m2m = self.save_m2m

        def save_m2m():
            old_save_m2m()
            base_dir = 'uploadtemplate/themes/{pk}/'.format(pk=instance.pk)

            names = set()

            # First unzip and replace any files.
            for filename in self._zip_file.namelist():
                output_path = filename[(len(self._zip_file_root) + 1):]
                name = os.path.join(base_dir, output_path)
                sio = StringIO()
                sio.write(self._zip_file.read(filename))
                fp = ContentFile(sio)
                if default_storage.exists(name):
                    default_storage.delete(name)
                default_storage.save(name, fp)
                names.add(name)

            # Then recursively delete any files that don't belong.
            def check_dir(root_dir):
                directories, files = default_storage.listdir(root_dir)
                for filename in files:
                    path = os.path.join(root_dir, filename)
                    if path not in names:
                        default_storage.delete(path)
                for dirname in directories:
                    path = os.path.join(root_dir, dirname)
                    check_dir(path)
            check_dir(base_dir)

        if commit:
            instance.save()
            save_m2m()
        else:
            self.save_m2m = save_m2m

        return instance
