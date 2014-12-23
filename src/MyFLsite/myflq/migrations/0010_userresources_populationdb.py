# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myflq', '0009_auto_20141222_1525'),
    ]

    operations = [
        migrations.AddField(
            model_name='userresources',
            name='populationdb',
            field=models.BooleanField(help_text='Check this box if this configuration will be used to build up\n        a population allele frequency table.', default=False, verbose_name='population database'),
            preserve_default=True,
        ),
    ]
