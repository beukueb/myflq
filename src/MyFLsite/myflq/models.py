from django.db import models
from django.utils.safestring import mark_safe

# Create your models here.

#Setup
##some symbols allowed in django username that are not allowed in MySQL name
noSQLname = {'@','+','-','.'}

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
class UserResources(models.Model):
    """
    This model indicates which databases the user has at their disposal.
    """
    user = models.ForeignKey(User)
    dbname = models.CharField(max_length=200,verbose_name="configuration name",
                              help_text='Choose a sensible name for your configuration',
         validators=[RegexValidator(regex=r'^\w*$', message='Should ony contain alphanumericals.')])
    description = models.TextField(verbose_name="configuration description",null=True,blank=True)
    lociFile = models.FileField(verbose_name='loci configuration file',
                                upload_to=lambda instance,filename: 'locifiles/'+instance.fulldbname()+'.csv',
                                help_text="The loci file should contain one line for every locus with the following structure:<br />\
                                LocusName,LocusType(a number for STR indicating repeat length or 'SNP' for other \
                                loci),forward primer, reverse primer")
    alleleFile = models.FileField(verbose_name='allele database file',
                                  upload_to=lambda instance,filename: 'allelefiles/'+instance.fulldbname()+'.csv',
                                  help_text="This file should contain all known alleles within the population. Each line should have\
                                  the following structure:<br />Locus name, STR number for STR loci/Allele name for SNP loci, Sequence")
    creationDate = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.dbname
        
    def dbusername(self):
        """
        This is the username for the database, linked to the MyFLsite current user 
        """
        if not set(self.user.username) & noSQLname:
            return 'myfls_'+self.user.username
        else:
            return 'myflsid_'+str(self.user.id)
    
    def fulldbname(self):
        """
        This is the name how it will be used in the database system.
        It includes a general MyFLsite prefix, and the username so that
        different users can use the same short dbname
        """
        return self.dbusername()+'_'+self.dbname
        
class Primer(models.Model):
    """
    This model lists all primers analyzed per database
    """
    dbname = models.ForeignKey(UserResources)
    locusName = models.CharField(max_length=200)
    locusType = models.IntegerField(null=True,blank=True,max_length=1,verbose_name='type')
    forwardPrimer = models.CharField(max_length=200)
    reversePrimer = models.CharField(max_length=200)
    
    class Meta:
        unique_together = ("dbname", "locusName")
    
    def __str__(self):
        return self.locusName
        
#Analysis
from django.core.exceptions import ValidationError
def validate_percentage(value):
    if value and not (0 < value <= 1):
        raise ValidationError('{} is not within [0-1]'.format(value))

import re, uuid
goodSeqFileRegex = re.compile(r'.*(\.fasta|\.fasta\.gz|\.fastq|\.fastq\.gz)$')
def generateFileName(instance,filename):
    instance.originalFilename = filename
    return 'fastqfiles/'+str(uuid.uuid4())+goodSeqFileRegex.match(filename).groups()[0]

class Analysis(models.Model):
    """
    Gathers all information for starting an analysis.
    """
    name = models.TextField(verbose_name="analysis name",null=True,blank=True)
    configuration = models.ForeignKey(UserResources)
    fastq = models.FileField(verbose_name="fast[a|q][.gz]",upload_to=generateFileName,blank=True,
                             validators=[RegexValidator(regex=goodSeqFileRegex, message='Only fast[a|q][gz] files.')],
                             help_text='''Provide the file either by uploading or by choosing a previously uploaded one.
                             A filename should end with either: .fasta, .fasta.gz, .fastq, or, .fastq.gz'''
    )
        #blank=True=>Form processing needs to make fastq required
    originalFilename = models.CharField(max_length=128,null=True)
    negativeReadsFilter = models.BooleanField(default=True,help_text=
        '''Long flanks could overlap within small unknown alleles, or their
        stutters. This option filters them, but reports on their abundance.'''
    )
    #kMerAssign = 
    primerBuffer = models.IntegerField(default=0,help_text=
                '''The ends of the primers are not used for assigning the reads
                to loci. Choosing a higher primerBuffer therefore means the
                locus assignment will be less specific, but more reads will be
                asigned.'''
    )
    flankOut = models.BooleanField(default=True,help_text=mark_safe(
                '''Options:<br />
                Flankout analysis. This analysis will only consider the region of interest
                of the different population alleles, based on the selected configuration
                allele database.<br /><br />
                Variant discovery. For population studies, where the scope is to find new
                variants, this option should be selected. It will report on all new variants
                discovered between the primers for the loci considered in the configuration.
                This option should also be chosen if you see a large amount of negative reads
                in a flankout analyis, or a high abundant unique read with very poor flanks.''')
    )
    stutterBuffer = models.IntegerField(default=1,help_text=
                '''The stutters of the smallest allele for a locus are normally not in
                the database. Default value of stutterBuffer is 1, which allows them to
                be seen in the analysis as flanking out is performed with a flank 1 repeat
                unit smaller.'''
    )
    useCompress = models.BooleanField(default=True,help_text=
                '''Homopolymers are a common problem for sequencing. With useCompress
                activated, flanks are removed taking account for possible homopolymer 
                issues.'''
    )
    withAlignment = models.BooleanField(default=False,help_text=
                '''If this option is activated, flanks are removed with our alignment
                algorithm, instead of the k-mer based flexible flanking.'''
    )
    threshold = models.FloatField(default=0.005,help_text=
                '''Unique reads with an abundance lower than this value, are discarded.
                It is reported how many reads were discarded in this way.'''
    )
    clusterInfo = models.BooleanField(default=True,help_text=
                '''With this option activated, unique reads within a loci are compared
                to each other. Reads that differ little are annotated as such.
                Does require more processing time.'''
    )
    randomSubset = models.FloatField(blank=True,null=True,validators=[validate_percentage], 
                help_text= '''Should be between 0 and 1, or blank.
                Indicates the percentage of the file that will be used for processing.
                This allows to get an initial quick analysis for low values.'''
    )
    progress = models.CharField(max_length=2,default='Q',choices=[('Q','Queued'),('P','Processing'),('F','Finished'),('FA','Failed')])
    creationTime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Analysis: config = '+str(self.configuration)+', file = '+self.originalFilename+' [settings => '+ \
            'negativeReadsFilter = '+str(self.negativeReadsFilter)+', '+ \
            'primerBuffer = '+str(self.primerBuffer)+', '+ \
            'flankOut = '+str(self.flankOut)+' ,'+ \
            'stutterBuffer = '+str(self.stutterBuffer)+', '+ \
            'useCompress = '+str(self.useCompress)+', '+ \
            'withAlignment = '+str(self.withAlignment)+', '+ \
            'threshold = '+str(self.threshold)+', '+ \
            'clusterInfo = '+str(self.clusterInfo)+', '+ \
            'randomSubset = '+str(self.randomSubset)+', '+ \
            'creationTime = '+str(self.creationTime)+']'

from time import strftime as st    
class AnalysisResults(models.Model):
    """
    One-to one linked with analysis. Info for post-processing.
    """
    analysis = models.OneToOneField(Analysis)
    xmlFile = models.FileField(upload_to=lambda instance,filename: st('resultfiles/%Y/%m/%d/')+
                               instance.analysis.configuration.fulldbname()+'.xml')
    figFile = models.ImageField(upload_to=lambda instance,filename: st('resultfiles/%Y/%m/%d/')+
                                instance.analysis.configuration.fulldbname()+'.png')
