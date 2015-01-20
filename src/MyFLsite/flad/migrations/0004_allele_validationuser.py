# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('flad', '0003_allele_fladid'),
    ]

    operations = [
        migrations.AddField(
            model_name='allele',
            name='validationUser',
            field=models.ForeignKey(null=True, related_name='vuser', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
