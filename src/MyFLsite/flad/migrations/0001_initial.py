# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Allele',
            fields=[
                ('id', models.PositiveIntegerField(verbose_name='FLADid', primary_key=True, serialize=False)),
                ('sequence', models.TextField(help_text='Allele sequence should only contain A,C,T or G, and N for masked bases', verbose_name='allele sequence', validators=[django.core.validators.RegexValidator(message='Should ony contain nucleotide letters A,C,T, or G, and N for masked bases.', regex='^[ACTGN]*$')], max_length=1000)),
                ('creationDate', models.DateField(auto_now_add=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
