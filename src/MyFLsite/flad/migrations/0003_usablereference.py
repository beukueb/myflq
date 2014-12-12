# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flad', '0002_auto_20141212_0909'),
    ]

    operations = [
        migrations.CreateModel(
            name='UsableReference',
            fields=[
                ('id', models.PositiveIntegerField(primary_key=True, serialize=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
