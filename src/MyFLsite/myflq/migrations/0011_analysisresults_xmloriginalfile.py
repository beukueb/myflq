# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import myflq.models


class Migration(migrations.Migration):

    dependencies = [
        ('myflq', '0010_userresources_populationdb'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysisresults',
            name='xmlOriginalFile',
            field=models.FileField(upload_to=myflq.models.xmlUpload, null=True),
            preserve_default=True,
        ),
    ]
