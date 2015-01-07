# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flad', '0004_fladkey'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestAllele',
            fields=[
                ('allele_ptr', models.OneToOneField(to='flad.Allele', serialize=False, auto_created=True, parent_link=True, primary_key=True)),
            ],
            options={
            },
            bases=('flad.allele',),
        ),
    ]
