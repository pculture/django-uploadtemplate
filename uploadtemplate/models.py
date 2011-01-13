from ConfigParser import ConfigParser
import os.path
import shutil
from StringIO import StringIO
import zipfile

from django.conf import settings
from django.core.signals import request_finished
from django.db import models
from django.dispatch import Signal

from uploadtemplate import _is_disabled

THEME_CACHE = None

class ThemeManager(models.Manager):

    def create_theme(self, *args, **kwargs):
        if 'name' in kwargs:
            name = original_name = kwargs['name']
            c = 1
            while self.filter(name=name):
                c += 1
                name = '%s %s' % (original_name, c)
            kwargs['name'] = name
        obj = self.create(*args, **kwargs)
        self.set_default(obj)
        return obj

    def set_default(self, obj):
        global THEME_CACHE
        for theme in self.filter(default=True):
            theme.default = False
            theme.save()

        obj.default = True
        obj.save()
        THEME_CACHE = obj

    def get_default(self):
        global THEME_CACHE
        if THEME_CACHE is None:
            THEME_CACHE = self.get(default=True)
        return THEME_CACHE

    def clear_cache(self):
        global THEME_CACHE
        THEME_CACHE = None

class Theme(models.Model):

    site = models.ForeignKey('sites.Site')
    name = models.CharField(max_length=255)
    thumbnail = models.ImageField(upload_to='uploadtemplate/theme_thumbnails',
                                  blank=True)
    description = models.TextField()
    default = models.BooleanField(default=False)

    bundled = models.BooleanField(default=False)

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

    def may_set_as_default(self):
        if self.bundled:
            return True # you may always choose a bundled theme
        else:
            if _is_disabled(): # Sorry! When the system is disabled
                return False   # you may only choose a bundled theme.
            return True

    def set_as_default(self):
        Theme.objects.set_default(self)

    def static_root(self):
        return '%s/static/%i/' % (settings.UPLOADTEMPLATE_MEDIA_ROOT, self.pk)

    def static_url(self):
        return '%s/static/%i/' % (settings.UPLOADTEMPLATE_MEDIA_URL, self.pk)

    def template_dir(self):
        return '%s/templates/%i/' % (settings.UPLOADTEMPLATE_MEDIA_ROOT,
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
            name = os.path.basename(self.thumbnail.name)
            config.set('Theme', 'thumbnail', name)
            zip_file.writestr('%s/%s' % (self.name.encode('utf8'),
                                         name.encode('utf8')),
                              self.thumbnail.read())

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
