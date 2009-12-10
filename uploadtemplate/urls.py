from django.conf.urls.defaults import *

urlpatterns = patterns(
    'uploadtemplate.views',
    (r'^$', 'index', {}, 'uploadtemplate-index'),
    (r'^set_default/(\d+)$', 'set_default', {}, 'uploadtemplate-set_default'),
    (r'^delete/(\d+)$', 'delete', {}, 'uploadtemplate-delete'),
    (r'^download/(\d+)$', 'download', {}, 'uploadtemplate-download')
    )
