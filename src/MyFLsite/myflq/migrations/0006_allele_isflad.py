# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myflq', '0005_auto_20141216_1552'),
    ]

    operations = [
        migrations.AddField(
            model_name='allele',
            name='isFLAD',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
