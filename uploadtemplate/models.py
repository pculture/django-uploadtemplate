from ConfigParser import ConfigParser
import os.path
import shutil
from StringIO import StringIO
import zipfile

from django.conf import settings
from django.db import models

class ThemeManager(models.Manager):

    _default_cache = None

    def create_theme(self, *args, **kwargs):
        obj = self.create(*args, **kwargs)
        self.set_default(obj)
        return obj

    def set_default(self, obj):
        if obj.default:
            return
        try:
            current_default = self.get_default()
        except obj.DoesNotExist:
            pass
        else:
            current_default.default = False
            current_default.save()

        obj.default = True
        obj.save()
        self._default_cache = obj

    def get_default(self):
        if self._default_cache is None:
            self._default_cache = self.get(default=True)
        return self._default_cache

class Theme(models.Model):

    site = models.ForeignKey('sites.Site')
    name = models.CharField(max_length=255)
    thumbnail = models.ImageField(upload_to='uploadtemplate/theme_thumbnails',
                                  blank=True)
    description = models.TextField()
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
        if self.default:
            # clear the cache
            Theme.objects._default_cache = None
        shutil.rmtree(self.static_root())
        shutil.rmtree(self.template_dir())
        models.Model.delete(self, *args, **kwargs)

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
            zip_file.writestr(name.encode('utf8'), self.thumbnail.read())

        meta_ini = StringIO()
        config.write(meta_ini)

        zip_file.writestr('meta.ini', meta_ini.getvalue())

        for zip_dir, root in (('static', self.static_root()),
                              ('templates', self.template_dir())):
            for dirname, dirs, files in os.walk(root):
                for filename in files:
                    fullpath = os.path.join(dirname, filename)
                    zip_file.write(fullpath, os.path.join(
                            zip_dir, fullpath[len(root):]))

        zip_file.close()
