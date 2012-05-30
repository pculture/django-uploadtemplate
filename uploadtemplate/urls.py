from django.conf.urls.defaults import url, patterns

from uploadtemplate.views import AdminView


urlpatterns = patterns('uploadtemplate.views',
    url(r'^$', AdminView.as_view(), name='uploadtemplate-index'),
    url(r'^unset_default$', 'unset_default', name='uploadtemplate-unset_default'),
    url(r'^set_default/(\d+)$', 'set_default', name='uploadtemplate-set_default'),
    url(r'^delete/(\d+)$', 'delete', name='uploadtemplate-delete'),
    url(r'^download/(\d+)$', 'download', name='uploadtemplate-download')
)
