import os
import shutil
import zipfile

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.signals import request_finished
from django.db import models


class ThemeManager(models.Manager):
    def __init__(self):
        super(ThemeManager, self).__init__()
        self._cache = {}

    def get_cached(self, site, using):
        if isinstance(site, Site):
            site = site.pk
        site_pk = int(site)
        if (using, site_pk) not in self._cache:
            try:
                theme = self.get(site=site_pk, default=True)
            except self.model.DoesNotExist:
                theme = None
            self._cache[(using, site_pk)] = theme
        theme = self._cache[(using, site_pk)]
        if theme is None:
            raise self.model.DoesNotExist
        return theme

    def get_current(self):
        """
        Shortcut for getting the currently-active instance from the cache.

        """
        site = settings.SITE_ID
        using = self._db if self._db is not None else 'default'
        return self.get_cached(site, using)

    def clear_cache(self):
        self._cache = {}

    def _post_save(self, sender, instance, created, raw, using, **kwargs):
        if instance.default:
            self._cache[(using, instance.site_id)] = instance
        elif ((using, instance.site_id) in self._cache and
              self._cache[(using, instance.site_id)] == instance):
            self._cache[(using, instance.site_id)] = None

    def contribute_to_class(self, model, name):
        # In addition to the normal contributions, we also attach a post-save
        # listener to cache newly-saved instances immediately. This is
        # post-save to make sure that we don't cache anything invalid.
        super(ThemeManager, self).contribute_to_class(model, name)
        if not model._meta.abstract:
            models.signals.post_save.connect(self._post_save, sender=model)


class Theme(models.Model):
    site = models.ForeignKey('sites.Site')
    name = models.CharField(max_length=255)
    theme_files_zip = models.FileField(upload_to='uploadtemplate/files/%Y/%m/%d',
                                       blank=True)
    thumbnail = models.ImageField(
                        upload_to='uploadtemplate/thumbnails/%Y/%m/%d',
                        blank=True)
    description = models.TextField(blank=True)
    default = models.BooleanField(default=False)

    objects = ThemeManager()

    def __unicode__(self):
        if self.default:
            return u'%s (default)' % self.name
        else:
            return self.name

    @models.permalink
    def get_absolute_url(self):
        return ['uploadtemplate-set_default', (self.pk,)]

    @property
    def theme_files_dir(self):
        if self.pk is None:
            raise AttributeError("Themes with no pk have no theme files directory.")
        return 'uploadtemplate/themes/{pk}/'.format(pk=self.pk)

    def save_files(self):
        zip_file = zipfile.ZipFile(self.theme_files_zip)

        # Unzip and replace any files.
        for filename in zip_file.namelist():
            # skip any zipped directories.
            if filename.endswith('/'):
                continue
            name = os.path.join(self.theme_files_dir, filename)
            fp = ContentFile(zip_file.read(filename))
            if default_storage.exists(name):
                default_storage.delete(name)
            default_storage.save(name, fp)

    def list_files(self, root_dir=None):
        if root_dir is None:
            root_dir = self.theme_files_dir
        directories, filenames = default_storage.listdir(root_dir)
        files = [os.path.join(root_dir, name) for name in filenames]
        for dirname in directories:
            files.extend(self.list_files(os.path.join(root_dir, dirname)))
        return files

    def prune_files(self):
        """
        Removes files from the theme's directory that aren't in the theme's
        zipfile.

        """
        zip_file = zipfile.ZipFile(self.theme_files_zip)

        expected_files = set((os.path.join(self.theme_files_dir, name)
                              for name in zip_file.namelist()))
        found_files = set(self.list_files())

        to_prune = found_files - expected_files
        for name in to_prune:
            default_storage.delete(name)

    def delete_files(self):
        """
        Removes all files from the theme's directory.

        """
        for name in self.list_files():
            default_storage.delete(name)

    def delete(self, *args, **kwargs):
        self.delete_files()
        # Backwards-compat: Try to delete the old directories too.
        try:
            shutil.rmtree(self.static_root())
        except OSError, e:
            if e.errno == 2: # no such file:
                pass
            else:
                raise
        try:
            shutil.rmtree(self.template_dir())
        except OSError, e:
            if e.errno == 2: # no such file
                pass
            else:
                raise
        Theme.objects._post_save(None, self, None, None, using=self._state.db)
        super(Theme, self).delete(self, *args, **kwargs)

    # Required for backwards-compatibility shims for get_static_url.
    def static_root(self):
        return '%sstatic/%i/' % (settings.UPLOADTEMPLATE_MEDIA_ROOT, self.pk)

    # Required for backwards-compatibility shims for get_static_url.
    def static_url(self):
        return '%sstatic/%i/' % (settings.UPLOADTEMPLATE_MEDIA_URL, self.pk)

    # Required for backwards-compatibility shims for template loader.
    def template_dir(self):
        return '%stemplates/%i/' % (settings.UPLOADTEMPLATE_MEDIA_ROOT,
                                     self.pk)

def finished(sender, **kwargs):
    Theme.objects.clear_cache()
request_finished.connect(finished)
