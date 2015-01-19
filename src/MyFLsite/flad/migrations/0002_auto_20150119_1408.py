# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flad', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='allele',
            name='locus',
            field=models.ForeignKey(null=True, to='flad.Locus'),
            preserve_default=True,
        ),
    ]
