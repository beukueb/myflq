# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flad', '0005_testallele'),
    ]

    operations = [
        migrations.AddField(
            model_name='allele',
            name='length',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
    ]
