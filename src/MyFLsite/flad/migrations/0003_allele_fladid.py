# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flad', '0002_auto_20150119_1408'),
    ]

    operations = [
        migrations.AddField(
            model_name='allele',
            name='fladid',
            field=models.PositiveIntegerField(null=True, verbose_name='FLADid'),
            preserve_default=True,
        ),
    ]
