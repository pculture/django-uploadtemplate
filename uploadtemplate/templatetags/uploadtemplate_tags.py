from __future__ import absolute_import

import warnings

from django import template

from uploadtemplate.templatetags.uploadtemplate import static


register = template.Library()


class GetStaticUrlNode(template.Node):
    def __init__(self, path):
        self.path = path

    def render(self, context):
        path = self.path.resolve(context)
        return static(context, path)


@register.tag
def get_static_url(parser, token):
    bits = token.split_contents()
    warnings.warn("{tag_name} is deprecated. Use uploadtemplate.static instead.".format(tag_name=bits[0]))
    if len(bits) == 3:
        warnings.warn("{tag_name} no longer takes a `bundled` kwarg".format(tag_name=bits[0]),
                      DeprecationWarning)
    elif len(bits) != 2:
        raise template.TemplateSyntaxError('{tag_name} takes 1 argument'.format(tag_name=bits[0]))

    return GetStaticUrlNode(parser.compile_filter(bits[1]))
