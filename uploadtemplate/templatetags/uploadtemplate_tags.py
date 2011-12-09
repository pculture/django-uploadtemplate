import urlparse

from django.conf import settings
from django import template

from uploadtemplate.models import Theme

register = template.Library()

class ThemeStaticUrlNode(template.Node):
    def __init__(self, path):
        self.path = path

    def render(self, context):
        if 'uploadtemplate_theme' in context:
            theme = context['uploadtemplate_current_theme']
        else:
            try:
                theme = Theme.objects.get_default()
            except Theme.DoesNotExist:
                theme = None
            context['uploadtemplate_current_theme'] = theme

        if theme is None:
            base = settings.STATIC_URL
        else:
            base = theme.static_url()

        path = self.path.resolve(context)
        if path.startswith('/') and not (theme and theme.bundled):
            path = path[1:]
        return urlparse.urljoin(base, path)

@register.tag
def get_static_url(parser, token):
    tokens = token.split_contents()
    if len(tokens) != 2:
        raise template.TemplateSyntaxError('%s takes 1 argument' % tokens[0])
    return ThemeStaticUrlNode(template.Variable(tokens[1]))
