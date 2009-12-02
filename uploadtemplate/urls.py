from django.conf.urls.defaults import *

urlpatterns = patterns(
    'uploadtemplate.views',
    (r'^$', 'index', {}, 'uploadtemplate-index'),
    (r'^(.+)$', 'access', {}, 'uploadtemplate-access'))
