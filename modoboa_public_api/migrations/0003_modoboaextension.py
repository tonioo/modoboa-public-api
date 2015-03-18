# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import versionfield


class Migration(migrations.Migration):

    dependencies = [
        ('modoboa_public_api', '0002_modoboainstance_last_request'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModoboaExtension',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('version', versionfield.VersionField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
