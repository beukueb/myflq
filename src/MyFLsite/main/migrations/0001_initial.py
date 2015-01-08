# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(verbose_name='email (*)', max_length=254)),
                ('firstname', models.CharField(null=True, verbose_name='first name', blank=True, max_length=200)),
                ('lastname', models.CharField(null=True, verbose_name='last name', blank=True, max_length=200)),
                ('institute', models.CharField(null=True, verbose_name='forensic institute/lab', blank=True, max_length=200)),
                ('fladRequest', models.BooleanField(verbose_name='request FLAD validation', default=False)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
