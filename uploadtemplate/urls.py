from django.conf.urls.defaults import url, patterns

from uploadtemplate.views import ThemeIndexView, ThemeCreateView, ThemeUpdateView


urlpatterns = patterns('uploadtemplate.views',
    url(r'^$', ThemeIndexView.as_view(), name='uploadtemplate-index'),
    url(r'^add/$', ThemeCreateView.as_view(), name='uploadtemplate-create'),
    url(r'^(?P<pk>\d+)/edit$', ThemeUpdateView.as_view(), name='uploadtemplate-edit'),
    # Backwards-compat - don't use pk kwarg here.
    url(r'^(\d+)/delete$', 'delete', name='uploadtemplate-delete'),
    url(r'^unset_default$', 'unset_default', name='uploadtemplate-unset_default'),
    url(r'^set_default/(\d+)$', 'set_default', name='uploadtemplate-set_default'),

    # Backwards-compat. Just 404s.
    url(r'^download/(\d+)$', 'download', name='uploadtemplate-download')
)
