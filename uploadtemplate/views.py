from __future__ import with_statement
import os

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response

from uploadtemplate import forms

def index(request):
    """
    If it's a POST request, we try to save the uploaded template.  Otherwise,
    show a list of the currently uploaded templates.
    """
    if request.method == 'POST':
        form = forms.TemplateUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(request.path)
    else:
        form = forms.TemplateUploadForm()

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
                               'templates': templates})

def access(request, template):
    full_path = os.path.join(settings.UPLOADTEMPLATE_MEDIA_ROOT, template)
    if not os.path.exists(full_path):
        raise Http404

    if request.method == 'GET':
        format = request.GET.get('format', 'html')
        with file(full_path, 'r') as template_file:
            if format == 'raw':
                return HttpResponse(template_file.read())
            else:
                return render_to_response('uploadtemplate/access.html',
                                      {'data': template_file.read(),
                                       'template': template})
    elif request.method == 'DELETE':
        os.remove(full_path)
        return HttpResponseRedirect(reverse('uploadtemplate-index'))
