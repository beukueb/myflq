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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sequence', models.TextField(validators=[django.core.validators.RegexValidator(regex='^[ACTGN]*$', message='Should ony contain nucleotide letters A,C,T, or G, and N for masked bases.')], verbose_name='allele sequence', help_text='Allele sequence should only contain A,C,T or G, and N for masked bases', max_length=1000)),
                ('length', models.PositiveIntegerField()),
                ('creationDate', models.DateField(auto_now_add=True)),
                ('validation', models.NullBooleanField(default=False)),
                ('doi', models.CharField(null=True, max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FLADkey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('FLADkey', models.CharField(max_length=50)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Locus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TestAllele',
            fields=[
                ('allele_ptr', models.OneToOneField(parent_link=True, serialize=False, to='flad.Allele', auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=('flad.allele',),
        ),
        migrations.AddField(
            model_name='allele',
            name='locus',
            field=models.ForeignKey(to='flad.Locus'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='allele',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
