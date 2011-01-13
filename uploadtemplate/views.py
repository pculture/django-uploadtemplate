from __future__ import with_statement
from StringIO import StringIO

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from uploadtemplate import forms
from uploadtemplate import models

def _is_disabled():
    # Get the value from settings
    disable_upload = getattr(settings, 'UPLOADTEMPLATE_DISABLE_UPLOAD', False)
    # If it is a callable, return its return value.
    if callable(disable_upload):
        return disable_upload()
    # Else, return whatever we got
    return disable_upload

def index(request):
    """
    If it's a POST request, we try to save the uploaded template.  Otherwise,
    show a list of the currently uploaded templates.
    """
    if request.method == 'POST':
        if _is_disabled():
            return HttpResponseForbidden()
        form = forms.ThemeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(request.path)
    else:
        form = forms.ThemeUploadForm()

    try:
        default = models.Theme.objects.get_default()
    except models.Theme.DoesNotExist:
        default = None

    return render_to_response('uploadtemplate/index.html',
                              {'form': form,
                               'default': default,
                               'themes': models.Theme.objects.all(),
                               'non_default_themes':
                                   models.Theme.objects.exclude(default=True),
                               },
                              context_instance=RequestContext(request))

def set_default(request, theme_id):
    '''This sets a theme as the default.
    
    Note that if the module is disabled through a settings option, you will
    only allowed to be permitted to select a "bundled" theme.'''
    theme = get_object_or_404(models.Theme, pk=theme_id)
    if theme.bundled:
        pass # good, everyone can use these
    else:
        if _is_disabled(): # check that custom themes are enabled
            return HttpResponseForbidden()

    # At this point, all authorization and validity checks have succeeded.
    theme.set_as_default()
    return HttpResponseRedirect(reverse('uploadtemplate-index'))

def delete(request, theme_id):
    theme = get_object_or_404(models.Theme, pk=theme_id)
    if theme.bundled:
         return HttpResponseForbidden("You may not delete a theme that comes bundled with the site.")
    theme.delete()
    return HttpResponseRedirect(reverse('uploadtemplate-index'))

def download(request, theme_id):
    theme = get_object_or_404(models.Theme, pk=theme_id)
    sio = StringIO()
    theme.zip_file(sio)
    sio.seek(0)
    response = HttpResponse(sio, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="%s.zip"' % (
        theme.name,)
    return response
