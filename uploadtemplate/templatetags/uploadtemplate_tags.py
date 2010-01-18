import urlparse

from django.conf import settings
from django import template

from uploadtemplate import models

register = template.Library()

class ThemeStaticUrlNode(template.Node):
    def __init__(self, path):
        self.path = path

    def render(self, context):
        if 'uploadtemplate_theme' in context:
            theme = context['uploadtemplate_theme']
            base = theme.static_url()
        else:
            try:
                theme = models.Theme.objects.get_default()
            except models.Theme.DoesNotExist:
                base = settings.MEDIA_URL
            else:
                context['uploadtemplate_theme'] = theme
                base = theme.static_url()
        return urlparse.urljoin(base, self.path.resolve(context))

@register.tag
def get_static_url(parser, token):
    tokens = token.split_contents()
    if len(tokens) != 2:
        raise template.TemplateSyntaxError('%s takes 1 argument' % tokens[0])
    return ThemeStaticUrlNode(template.Variable(tokens[1]))
