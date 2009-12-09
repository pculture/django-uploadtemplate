from __future__ import with_statement
import os

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404

from uploadtemplate import forms
from uploadtemplate import models

def index(request):
    """
    If it's a POST request, we try to save the uploaded template.  Otherwise,
    show a list of the currently uploaded templates.
    """
    if request.method == 'POST':
        form = forms.ThemeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(request.path)
    else:
        form = forms.ThemeUploadForm()

    templates = []
    for dirpath, dirnames, filenames in os.walk(
        settings.UPLOADTEMPLATE_MEDIA_ROOT):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            short_path = full_path[len(settings.UPLOADTEMPLATE_MEDIA_ROOT):]
            if short_path[0] == os.sep:
                short_path = short_path[1:]
            templates.append(short_path)

    return render_to_response('uploadtemplate/index.html',
                              {'form': form,
                               'default': models.Theme.objects.get_default(),
                               'themes': models.Theme.objects.all(),
                               'non_default_themes':
                                   models.Theme.objects.exclude(default=True),
                               })

def set_default(request, theme_id):
    theme = get_object_or_404(models.Theme, pk=theme_id)
    theme.set_as_default()
    return HttpResponseRedirect(reverse('uploadtemplate-index'))
