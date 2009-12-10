from django.template import TemplateDoesNotExist
from django.template.loaders import filesystem

from uploadtemplate import models

def load_template_source(template_name, dirs=None):
    try:
        theme = models.Theme.objects.get_default()
    except models.Theme.DoesNotExist:
        raise TemplateDoesNotExist, 'no default theme'

    return filesystem.load_template_source(template_name,
                                           [theme.template_dir()])
load_template_source.is_usable = True
