# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myflq', '0006_allele_isflad'),
    ]

    operations = [
        migrations.AddField(
            model_name='userresources',
            name='lastUpDate',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
