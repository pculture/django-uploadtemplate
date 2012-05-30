from __future__ import with_statement
from StringIO import StringIO

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic import FormView

from uploadtemplate.forms import ThemeUploadForm
from uploadtemplate.models import Theme


class AdminView(FormView):
    form_class = ThemeUploadForm
    template_name = 'uploadtemplate/index.html'

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super(AdminView, self).get_context_data(**kwargs)
        try:
            default = Theme.objects.get_default()
        except Theme.DoesNotExist:
            default = None

        context.update({
            'default': default,
            'themes': Theme.objects.all(),
        })
        return context

    def form_valid(self, form):
        form.save()
        return super(AdminView, self).form_valid(form)


def unset_default(request):
    '''
    This removes any them as set, to fall back to the default templates.
    '''
    Theme.objects.set_default(None)
    return HttpResponseRedirect(reverse('uploadtemplate-index'))


def set_default(request, theme_id):
    """Sets a theme as the default."""
    theme = get_object_or_404(Theme, pk=theme_id)
    theme.set_as_default()
    return HttpResponseRedirect(reverse('uploadtemplate-index'))


def delete(request, theme_id):
    theme = get_object_or_404(Theme, pk=theme_id)
    if theme.bundled:
         return HttpResponseForbidden("You may not delete a theme that comes bundled with the site.")
    theme.delete()
    return HttpResponseRedirect(reverse('uploadtemplate-index'))


def download(request, theme_id):
    theme = get_object_or_404(Theme, pk=theme_id)
    sio = StringIO()
    theme.zip_file(sio)
    sio.seek(0)
    response = HttpResponse(sio, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="%s.zip"' % (
        theme.name,)
    return response
