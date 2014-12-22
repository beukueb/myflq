# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myflq', '0007_userresources_lastupdate'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('inAlleleDatabase', models.BooleanField(default=False)),
                ('alleles', models.ManyToManyField(to='myflq.Allele')),
                ('analysis', models.OneToOneField(to='myflq.Analysis')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
