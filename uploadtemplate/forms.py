import zipfile

from django import forms
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError

from uploadtemplate.models import Theme


class ThemeForm(forms.ModelForm):
    class Meta:
        model = Theme
        exclude = ('site',)

    def clean_theme_files_zip(self):
        value = self.cleaned_data.get('theme_files_zip')
        if not value:
            return value

        if not zipfile.is_zipfile(value):
            raise ValidationError('Must be a valid zip archive.')

        try:
            zip_file = zipfile.ZipFile(value)
        except zipfile.error:
            raise ValidationError('Must be a valid zip archive.')

        names = zip_file.namelist()
        if not names:
            raise ValidationError('Zip archive cannot be empty.')

        for n in names:
            if n.startswith('/') or '..' in n.split('/'):
                raise ValidationError('Zip archive contains invalid names.')

        return value

    def save(self, commit=True):
        if not self.is_valid():
            raise ValueError("Cannot save an invalid upload.")

        self.instance.site = Site.objects.get_current()
        instance = super(ThemeForm, self).save(commit=False)

        old_save_m2m = self.save_m2m

        def save_m2m():
            old_save_m2m()
            instance.save_files()
            instance.prune_files()

        if commit:
            instance.save()
            save_m2m()
        else:
            self.save_m2m = save_m2m

        return instance
