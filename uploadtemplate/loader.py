import os

from django.core.files.storage import default_storage
from django.template import TemplateDoesNotExist
from django.template.loaders import filesystem

from uploadtemplate import models

class Loader(filesystem.Loader):
    def load_template_source(self, template_name, dirs=None):
        try:
            theme = models.Theme.objects.get_default()
        except models.Theme.DoesNotExist:
            raise TemplateDoesNotExist, 'no default theme'

        # Try the new location first.
        base_dir = 'uploadtemplate/themes/{pk}/templates'.format(pk=theme.pk)
        name = os.path.join(base_dir, template_name)
        if default_storage.exists(name):
            fp = default_storage.open(name)
            return (fp.read(), name)

        # Then fall back on the old location.
        return filesystem.Loader.load_template_source(
            self, template_name, [theme.template_dir()])

    load_template_source.is_usable = True

_loader = Loader()

def load_template_source(template_name, dirs=None):
    import warnings
    warnings.warn("`uploadtemplate.loader.load_template_source` is deprecated. "
                 "Use `uploadtemplate.loader.Loader` instead.",
                 DeprecationWarning)
    return _loader.load_template_source(template_name, dirs)
load_template_source.is_usable = True
