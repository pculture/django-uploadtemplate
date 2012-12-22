# -*- coding: utf-8 -*-
import datetime
import os
from StringIO import StringIO
import zipfile

from south.db import db
from south.v2 import DataMigration
from django.conf import settings
from django.db import models
from django.core.files.base import File, ContentFile
from django.core.files.storage import default_storage
from django.utils.encoding import force_unicode, smart_str


class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Remember to use orm['appname.ModelName'] rather than "from appname.models..."
        # This has two responsibilities:
        # 1. copy old template/static directories to themes/<pk>/*
        # 2. create a zipped version of those directories and save it to the
        #    Theme object.
        old_template = '{path}{dirname}/{pk}/'
        new_template = 'uploadtemplate/themes/{pk}/{dirname}/'
        dirnames = ('templates', 'static')
        upload_to = 'uploadtemplate/files/%Y/%m/%d'

        for theme in orm['uploadtemplate.Theme'].objects.all():
            sio = StringIO()
            zip_file = zipfile.ZipFile(sio, 'w')
            try:
                for dirname in dirnames:
                    format_kwargs = {'path': settings.UPLOADTEMPLATE_MEDIA_ROOT,
                                     'pk': theme.pk,
                                     'dirname': dirname}
                    old = old_template.format(**format_kwargs)
                    new = new_template.format(**format_kwargs)
                    for dir_path, dirs, files in os.walk(old):
                        for filename in files:
                            old_path = os.path.join(dir_path, filename)
                            name = old_path[len(old):]
                            new_path = os.path.join(new, name)
                            zip_path = os.path.join(dirname, name)
                            with open(old_path, 'r') as fp:
                                f = File(fp)
                                if default_storage.exists(new_path):
                                    default_storage.delete(new_path)
                                default_storage.save(new_path, f)
                            zip_file.write(old_path, zip_path)
            finally:
                zip_file.close()

            sio.seek(0)
            directory_name = os.path.normpath(force_unicode(datetime.datetime.now().strftime(smart_str(upload_to))))
            filename = os.path.normpath(default_storage.get_valid_name(os.path.basename('theme.zip')))
            name = os.path.join(directory_name, filename)
            name = default_storage.save(name, ContentFile(sio.read()))
            theme.theme_files_zip = name
            theme.save()

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'uploadtemplate.theme': {
            'Meta': {'object_name': 'Theme'},
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'theme_files_zip': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'})
        }
    }

    complete_apps = ['uploadtemplate']
    symmetrical = True
