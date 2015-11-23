# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myflq', '0013_analysisresults_updating'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysis',
            name='kMerAssign',
            field=models.IntegerField(default=0, help_text='Reads can be assigned to loci by looking up the presence\n                of primer kmers in the read. This allows for processing of\n                reads with errors in the primers. Default value: 0 == not using it.\n                When using, recommended values are 5,6,...'),
        ),
        migrations.AlterField(
            model_name='locus',
            name='locusType',
            field=models.IntegerField(verbose_name='type', blank=True, null=True),
        ),
    ]
