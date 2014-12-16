# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myflq', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='fladconfig',
            name='FLAD',
            field=models.CharField(help_text='Domain name for your FLAD provider. E.g. forensic.ugent.be', verbose_name='FLADprovider', max_length=200, default='forensic.ugent.be'),
            preserve_default=True,
        ),
    ]
