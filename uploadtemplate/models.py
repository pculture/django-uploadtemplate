from ConfigParser import ConfigParser
import os.path
import shutil
from StringIO import StringIO
import zipfile

from django.conf import settings
from django.db import models

class ThemeManager(models.Manager):


    def create_theme(self, *args, **kwargs):
        obj = self.create(*args, **kwargs)
        self.set_default(obj)
        return obj

    def set_default(self, obj):
        for theme in self.filter(default=True):
            theme.default = False
            theme.save()

        obj.default = True
        obj.save()

    def get_default(self):
        return self.get(default=True)

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
