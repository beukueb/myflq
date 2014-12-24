# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myflq', '0011_analysisresults_xmloriginalfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='minimalReads',
            field=models.IntegerField(help_text='Minimal amount of reads that was required for alleles to be in profile', default=0),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='profile',
            name='threshold',
            field=models.FloatField(help_text='Abundance threshold applied when profile was generated from resultxml', default=0),
            preserve_default=True,
        ),
    ]
