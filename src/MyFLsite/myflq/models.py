from django.db import models

# Create your models here.

#Setup
from django.contrib.auth.models import User
class UserResources(models.Model):
    """
    This model indicates which databases the user has at their disposal.
    """
    user = models.ForeignKey(User)
    dbname = models.CharField(max_length=200)
    isAlreadyCommitted = models.BooleanField(default=False)
    creationDate = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return self.dbname
        
    def dbusername(self):
        """
        This is the username for the database, linked to the MyFLsite current user 
        """
        return 'myfls_'+self.user.username
    
    def fulldbname(self):
        """
        This is the name how it will be used in the database system.
        It includes a general MyFLsite prefix, and the username so that
        different users can use the same short dbname
        """
        return 'myfls_'+self.user.username+'_'+self.dbname
        
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
        
class AlleleFiles(models.Model):
    """
    One instance extends UserResources pointing to an allele file that can
    be used to populate the MyFLq relevant database
    """
    dbname = models.OneToOneField(UserResources)
    alleleFile = models.FileField(upload_to=lambda instance,filename: 'allelefiles/'+instance.dbname.fulldbname()+'.csv')
    
    def __str__(self):
        return self.alleleFile.url
        

#Analysis
from django.core.exceptions import ValidationError
def validate_percentage(value):
    if value and not (0 < value <= 1):
        raise ValidationError('{} is not within [0-1]'.format(value))

def generateFileName(instance,filename):
    instance.originalFilename = filename
    return 'fastqfiles/'+instance.dbname.fulldbname()+'.fastq'

class Analysis(models.Model):
    """
    Gathers all information for starting an analysis.
    """
    dbname = models.ForeignKey(UserResources)
    fastq = models.FileField(upload_to=generateFileName,blank=True,
                             help_text='''Provide the fastq file either by uploading or by choosing a previously uploaded file.'''
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
    flankOut = models.BooleanField(default=True,help_text=
                '''If you see a large amount of negative reads in the analyis, or
                a high abundant unique reads with very poor flanks, turn off flankOut.
                The analysis will then be done between the primers. Previously unknown
                alleles can be discovered this way.'''
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
    creationTime = models.TimeField(auto_now_add=True)

    def __str__(self):
        return 'Analysis: db = '+str(self.dbname)+', file = '+self.originalFilename+' [settings => '+ \
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
    xmlFile = models.FileField(upload_to=lambda instance,filename: st('resultfiles/%Y/%m/%d/')+instance.analysis.dbname.fulldbname()+'.xml')
    figFile = models.ImageField(upload_to=lambda instance,filename: st('resultfiles/%Y/%m/%d/')+instance.analysis.dbname.fulldbname()+'.png')
