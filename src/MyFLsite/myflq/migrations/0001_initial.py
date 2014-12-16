# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import myflq.models
from django.conf import settings
import django.core.validators
import re


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Allele',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(blank=True, null=True, max_length=200)),
                ('repeatNumber', models.IntegerField(blank=True, verbose_name='type', null=True, max_length=2)),
                ('sequence', models.CharField(max_length=1000)),
                ('timeAdded', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Analysis',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.TextField(blank=True, null=True, verbose_name='analysis name')),
                ('fastq', models.FileField(blank=True, validators=[django.core.validators.RegexValidator(regex=re.compile('.*(\\.fasta|\\.fasta\\.gz|\\.fastq|\\.fastq\\.gz)$', 32), message='Only fast[a|q][gz] files.')], verbose_name='fast[a|q][.gz]', help_text='Provide the file either by uploading or by choosing a previously uploaded one.\n                             A filename should end with either: .fasta, .fasta.gz, .fastq, or, .fastq.gz', upload_to=myflq.models.generateFileName)),
                ('originalFilename', models.CharField(max_length=128, null=True)),
                ('negativeReadsFilter', models.BooleanField(default=True, help_text='Long flanks could overlap within small unknown alleles, or their\n        stutters. This option filters them, but reports on their abundance.')),
                ('primerBuffer', models.IntegerField(default=0, help_text='The ends of the primers are not used for assigning the reads\n                to loci. Choosing a higher primerBuffer therefore means the\n                locus assignment will be less specific, but more reads will be\n                asigned.')),
                ('flankOut', models.BooleanField(default=True, help_text='Options:<br />\n                Flankout analysis. This analysis will only consider the region of interest\n                of the different population alleles, based on the selected configuration\n                allele database.<br /><br />\n                Variant discovery. For population studies, where the scope is to find new\n                variants, this option should be selected. It will report on all new variants\n                discovered between the primers for the loci considered in the configuration.\n                This option should also be chosen if you see a large amount of negative reads\n                in a flankout analyis, or a high abundant unique read with very poor flanks.')),
                ('stutterBuffer', models.IntegerField(default=1, help_text='The stutters of the smallest allele for a locus are normally not in\n                the database. Default value of stutterBuffer is 1, which allows them to\n                be seen in the analysis as flanking out is performed with a flank 1 repeat\n                unit smaller.')),
                ('useCompress', models.BooleanField(default=True, help_text='Homopolymers are a common problem for sequencing. With useCompress\n                activated, flanks are removed taking account for possible homopolymer \n                issues.')),
                ('withAlignment', models.BooleanField(default=False, help_text='If this option is activated, flanks are removed with our alignment\n                algorithm, instead of the k-mer based flexible flanking.')),
                ('threshold', models.FloatField(default=0.005, help_text='Unique reads with an abundance lower than this value, are discarded.\n                It is reported how many reads were discarded in this way.')),
                ('clusterInfo', models.BooleanField(default=True, help_text='With this option activated, unique reads within a loci are compared\n                to each other. Reads that differ little are annotated as such.\n                Does require more processing time.')),
                ('randomSubset', models.FloatField(blank=True, validators=[myflq.models.validate_percentage], help_text='Should be between 0 and 1, or blank.\n                Indicates the percentage of the file that will be used for processing.\n                This allows to get an initial quick analysis for low values.', null=True)),
                ('progress', models.CharField(choices=[('Q', 'Queued'), ('P', 'Processing'), ('F', 'Finished'), ('FA', 'Failed')], max_length=2, default='Q')),
                ('creationTime', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-creationTime'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AnalysisResults',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('xmlFile', models.FileField(upload_to=myflq.models.xmlUpload)),
                ('figFile', models.ImageField(upload_to=myflq.models.pngUpload)),
                ('analysis', models.OneToOneField(to='myflq.Analysis')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FLADconfig',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('FLADname', models.CharField(max_length=30)),
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
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('locusType', models.IntegerField(blank=True, verbose_name='type', null=True, max_length=1)),
                ('forwardPrimer', models.CharField(max_length=200)),
                ('reversePrimer', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserResources',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('dbname', models.CharField(max_length=200, validators=[django.core.validators.RegexValidator(regex='^\\w*$', message='Should ony contain alphanumericals.')], help_text='Choose a sensible name for your configuration', verbose_name='configuration name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='configuration description')),
                ('lociFile', models.FileField(upload_to=myflq.models.lociUpload, help_text="The loci file should contain one line for every locus with the following structure:<br />                                LocusName,LocusType(a number for STR indicating repeat length or 'SNP' for other                                 loci),forward primer, reverse primer", verbose_name='loci configuration file')),
                ('alleleFile', models.FileField(upload_to=myflq.models.alleleUpload, help_text='This file should contain all known alleles within the population. Each line should have                                  the following structure:<br />Locus name, STR number for STR loci/Allele name for SNP loci, Sequence', verbose_name='allele database file')),
                ('creationDate', models.DateField(auto_now_add=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='locus',
            name='configuration',
            field=models.ForeignKey(to='myflq.UserResources'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='locus',
            unique_together=set([('configuration', 'name')]),
        ),
        migrations.AddField(
            model_name='analysis',
            name='configuration',
            field=models.ForeignKey(to='myflq.UserResources'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='allele',
            name='analysis',
            field=models.ForeignKey(null=True, blank=True, to='myflq.Analysis'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='allele',
            name='configuration',
            field=models.ForeignKey(to='myflq.UserResources'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='allele',
            name='locus',
            field=models.ForeignKey(to='myflq.Locus'),
            preserve_default=True,
        ),
    ]
