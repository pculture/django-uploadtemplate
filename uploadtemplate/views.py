from django.conf import settings
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView

from uploadtemplate.forms import ThemeForm
from uploadtemplate.models import Theme


class ThemeCreateView(CreateView):
    form_class = ThemeForm
    template_name = 'uploadtemplate/theme_edit.html'
    success_url = reverse_lazy('uploadtemplate-index')
    context_object_name = 'theme'
    initial = {'default': True}

    def get_queryset(self):
        return Theme.objects.filter(site=settings.SITE_ID)


class ThemeUpdateView(UpdateView):
    form_class = ThemeForm
    template_name = 'uploadtemplate/theme_edit.html'
    success_url = reverse_lazy('uploadtemplate-index')
    context_object_name = 'theme'

    def get_queryset(self):
        return Theme.objects.filter(site=settings.SITE_ID)


class ThemeIndexView(ListView):
    template_name = 'uploadtemplate/theme_index.html'
    context_object_name = 'themes'

    def get_queryset(self):
        return Theme.objects.filter(site=settings.SITE_ID)

    def get_context_data(self, **kwargs):
        context = super(ThemeIndexView, self).get_context_data(**kwargs)
        try:
            current = Theme.objects.get_current()
        except Theme.DoesNotExist:
            current = None

        context.update({
            'current': current,
            # Backwards-compat
            'default': current,
        })
        return context


index = ThemeIndexView.as_view() # backwards compatibility


def unset_default(request):
    '''
    This removes any them as set, to fall back to the default templates.
    '''
    Theme.objects.filter(site=settings.SITE_ID, default=True).update(default=False)
    Theme.objects.clear_cache()
    return HttpResponseRedirect(reverse('uploadtemplate-index'))


def set_default(request, theme_id):
    """Sets a theme as the default."""
    theme = get_object_or_404(Theme, pk=theme_id)
    if not theme.default:
        Theme.objects.filter(site=settings.SITE_ID, default=True).update(default=False)
        theme.default = True
        theme.save()
    return HttpResponseRedirect(reverse('uploadtemplate-index'))


def delete(request, theme_id):
    theme = get_object_or_404(Theme, pk=theme_id)
    theme.delete()
    return HttpResponseRedirect(reverse('uploadtemplate-index'))


def download(request, theme_id):
    raise Http404
