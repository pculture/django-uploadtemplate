from django.template import TemplateDoesNotExist
from django.template.loaders import filesystem

from uploadtemplate import models

class Loader(filesystem.Loader):
    def load_template_source(self, template_name, dirs=None):
        try:
            theme = models.Theme.objects.get_default()
        except models.Theme.DoesNotExist:
            raise TemplateDoesNotExist, 'no default theme'

        return filesystem.Loader.load_template_source(
            self, template_name, [theme.template_dir()])

    load_template_source.is_usable = True

_loader = Loader()

def load_template_source(template_name, dirs=None):
    import warning
    warning.warn("`uploadtemplate.loader.load_template_source` is deprecated. "
                 "Use `uploadtempalte.loader.Loader` instead.",
                 DeprecationWarning)
    return _loader.load_template_source(template_name, dirs)
load_template_source.is_usable = True
