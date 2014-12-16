# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import myflq.models


class Migration(migrations.Migration):

    dependencies = [
        ('myflq', '0002_fladconfig_flad'),
    ]

    operations = [
        migrations.AlterField(
            model_name='allele',
            name='analysis',
            field=models.ForeignKey(to='myflq.Analysis', blank=True, related_name='first_reporting_analysis', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='allele',
            name='name',
            field=models.CharField(max_length=200, default='NA'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='allele',
            name='repeatNumber',
            field=models.FloatField(verbose_name='repeat number', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='allele',
            name='sequence',
            field=models.CharField(max_length=1000, default=''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresources',
            name='alleleFile',
            field=models.FileField(verbose_name='allele database file', upload_to=myflq.models.alleleUpload, blank=True, null=True, help_text='This file should contain all known alleles within the population. Each line should have                                  the following structure:<br />Locus name, STR number for STR loci/Allele name for SNP loci, Sequence'),
            preserve_default=True,
        ),
    ]
