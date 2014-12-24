# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myflq', '0012_auto_20141224_1141'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysisresults',
            name='updating',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
