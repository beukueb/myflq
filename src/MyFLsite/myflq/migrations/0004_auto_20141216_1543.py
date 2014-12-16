# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myflq', '0003_auto_20141216_1530'),
    ]

    operations = [
        migrations.AddField(
            model_name='allele',
            name='FLADid',
            field=models.CharField(default='FAXXX', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='allele',
            name='initialPopstat',
            field=models.FloatField(blank=True, verbose_name='initial population statistic', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='allele',
            name='popstat',
            field=models.FloatField(verbose_name='population statistic', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='allele',
            name='reports',
            field=models.ManyToManyField(to='myflq.Analysis'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='locus',
            name='refmask',
            field=models.CharField(blank=True, null=True, max_length=1000),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='locus',
            name='refnumber',
            field=models.FloatField(blank=True, verbose_name='reference repeat number', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='locus',
            name='refsequence',
            field=models.CharField(blank=True, null=True, max_length=1000),
            preserve_default=True,
        ),
    ]
