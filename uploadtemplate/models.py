from ConfigParser import ConfigParser
import os.path
import logging
import shutil
from StringIO import StringIO
import zipfile

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.signals import request_finished
from django.db import models
from django.dispatch import Signal


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
        elif self._cache[(using, instance.site_id)] == instance:
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

    def delete(self, *args, **kwargs):
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
        Theme.objects.clear_cache()
        models.Model.delete(self, *args, **kwargs)

    def static_root(self):
        return '%sstatic/%i/' % (settings.UPLOADTEMPLATE_MEDIA_ROOT, self.pk)

    def static_url(self):
        return '%sstatic/%i/' % (settings.UPLOADTEMPLATE_MEDIA_URL, self.pk)

    def template_dir(self):
        return '%stemplates/%i/' % (settings.UPLOADTEMPLATE_MEDIA_ROOT,
                                     self.pk)

    def zip_file(self, file_object):
        """
        Writes the ZIP file for this theme to file_object.
        """
        zip_file = zipfile.ZipFile(file_object, 'w')
        config = ConfigParser()
        config.add_section('Theme')
        config.set('Theme', 'name', self.name)
        config.set('Theme', 'description', self.description)
        if self.thumbnail:
            try:
                name = os.path.basename(self.thumbnail.name)
                thumbnail_data = self.thumbnail.read()
            except IOError, e:
                # For some reason, we could not download the thumbnail
                # data.
                logging.error(e)
                logging.error("We failed to grab a theme thumbnail.")
            else:
                # If we successfully got the thumbnail, add it to the zip.
                config.set('Theme', 'thumbnail', name)
                zip_file.writestr('%s/%s' % (self.name.encode('utf8'),
                                             name.encode('utf8')),
                                  thumbnail_data)

        meta_ini = StringIO()
        config.write(meta_ini)

        zip_file.writestr('%s/meta.ini' % self.name.encode('ascii'),
                          meta_ini.getvalue())

        data_paths = [('static', path) for path in
                      getattr(settings, 'UPLOADTEMPLATE_STATIC_ROOTS', [])]
        data_paths.extend([
                ('templates', path) for path in
                getattr(settings, 'UPLOADTEMPLATE_TEMPLATE_ROOTS', [])])
        data_paths.append(('static', self.static_root()))
        data_paths.append(('templates', self.template_dir()))

        zip_files = {}
        for zip_dir, root in data_paths:
            for dirname, dirs, files in os.walk(root):
                for filename in files:
                    fullpath = os.path.join(dirname, filename)
                    endpath = fullpath[len(root):]
                    if endpath[0] == '/':
                        endpath = endpath[1:]
                    zip_files[os.path.join(self.name.encode('utf8'),
                                       zip_dir, endpath)] = fullpath

        for callback, response in pre_zip.send(sender=self,
                                               file_paths=zip_files):
            for path in response:
                if path in zip_files:
                    del zip_files[path]

        for zippath, fullpath in zip_files.items():
            zip_file.write(fullpath, zippath)

        zip_file.close()

pre_zip = Signal(providing_args=['file_paths'])

def finished(sender, **kwargs):
    Theme.objects.clear_cache()
request_finished.connect(finished)
