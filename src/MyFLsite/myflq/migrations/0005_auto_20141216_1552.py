# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myflq', '0004_auto_20141216_1543'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='allele',
            unique_together=set([('configuration', 'locus', 'FLADid')]),
        ),
    ]
