import urlparse

from django.conf import settings
from django import template

from uploadtemplate.models import Theme

register = template.Library()

class ThemeStaticUrlNode(template.Node):
    def __init__(self, path, use_bundled):
        self.path = path
        self.use_bundled = use_bundled

    def render(self, context):
        if 'uploadtemplate_theme' in context:
            theme = context['uploadtemplate_current_theme']
        else:
            try:
                theme = Theme.objects.get_default()
            except Theme.DoesNotExist:
                theme = None
            context['uploadtemplate_current_theme'] = theme

        path = self.path.resolve(context)
        if path.startswith('/'): # use_bundled = True and not (theme and theme.bundled):
            path = path[1:]
            use_bundled = True
        else:
            use_bundled = self.use_bundled

        if theme is None or use_bundled:
            base = settings.STATIC_URL
        else:
            base = theme.static_url()

        return urlparse.urljoin(base, path)

@register.tag
def get_static_url(parser, token):
    tokens = token.split_contents()
    if len(tokens) not in (2, 3):
        raise template.TemplateSyntaxError('%s takes 1 or 2 arguments' % tokens[0])
    use_bundled = False
    if len(tokens) == 3:
        if tokens[2] == 'bundled':
            use_bundled = True
        else:
            raise template.TemplateSyntaxError('%s 3rd argument must be "bundled", not %r' % (tokens[0], tokens[2]))
    return ThemeStaticUrlNode(template.Variable(tokens[1]),
                              use_bundled)
