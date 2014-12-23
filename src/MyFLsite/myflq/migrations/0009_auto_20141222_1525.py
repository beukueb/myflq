# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myflq', '0008_profile'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='allele',
            options={'ordering': ('locus',)},
        ),
        migrations.AlterModelOptions(
            name='locus',
            options={'ordering': ('name',)},
        ),
        migrations.AddField(
            model_name='profile',
            name='threshold',
            field=models.FloatField(help_text='Threshold applied when profile was generated from resultxml', default=0),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='analysis',
            name='flankOut',
            field=models.BooleanField(help_text='Options:<br />\n                Flankout analysis. This analysis will only consider the region of interest\n                of the different population alleles, based on the selected configuration\n                allele database.<br /><br />\n                Variant discovery. For population studies, where the scope is to find new\n                variants, this option should be selected. It will report on all new variants\n                discovered between the primers for the loci considered in the configuration.\n                This option should also be chosen if you see a large amount of negative reads\n                in a flankout analyis, or a high abundant unique read with very poor flanks.', default=False),
            preserve_default=True,
        ),
    ]
