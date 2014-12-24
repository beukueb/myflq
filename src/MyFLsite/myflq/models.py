from django.db import models
from django.utils.safestring import mark_safe

# Create your models here.

#Setup
##some symbols allowed in django username that are not allowed in MySQL name
noSQLname = {'@','+','-','.'}

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
#Previous lambda functions that needed to be named for migrations to work
def lociUpload(instance,filename): return 'locifiles/'+instance.fulldbname()+'.csv'
def alleleUpload(instance,filename): return 'allelefiles/'+instance.fulldbname()+'.csv'
class UserResources(models.Model):
    """
    This model indicates which databases the user has at their disposal.
    """
    user = models.ForeignKey(User)
    dbname = models.CharField(max_length=200,verbose_name="configuration name",
                              help_text='Choose a sensible name for your configuration',
         validators=[RegexValidator(regex=r'^\w*$', message='Should ony contain alphanumericals.')])
    description = models.TextField(verbose_name="configuration description",null=True,blank=True)
    populationdb = models.BooleanField(default=False,verbose_name='population database',help_text=
        '''Check this box if this configuration will be used to build up
        a population allele frequency table.'''
    )
    lociFile = models.FileField(verbose_name='loci configuration file',
                                upload_to=lociUpload,
                                help_text="The loci file should contain one line for every locus with the following structure:<br />\
                                LocusName,LocusType(a number for STR indicating repeat length or 'SNP' for other \
                                loci),forward primer, reverse primer")
    alleleFile = models.FileField(verbose_name='allele database file',
                                  null=True,blank=True,#With new config format all necessary info can be in lociFile for first analyses
                                  upload_to=alleleUpload,
                                  help_text="This file should contain all known alleles within the population. Each line should have\
                                  the following structure:<br />Locus name, STR number for STR loci/Allele name for SNP loci, Sequence")
    creationDate = models.DateField(auto_now_add=True)
    lastUpDate = models.DateTimeField(null=True,blank=True) #creationTime from last Allele added, to check if config needs updating

    def __str__(self):
        return self.dbname
        
    def dbusername(self):
        """
        This is the username for the database, linked to the MyFLsite current user 
        """
        if (not set(self.user.username) & noSQLname) and len(self.user.username) <= 10:
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

    def countNonValidatedAlleles(self):
        """
        This counts the number of NA or non validated alleles.
        It is not good practice to have too many such alleles linked to a configuration.
        Profiles that report such NA alleles should be tracked, and the NA allele
        should either be validated and get a FLADid or be removed from the profile.
        """
        return NotImplemented
    
class Locus(models.Model):
    """
    This model lists all loci analyzed per configuration
    """
    configuration = models.ForeignKey(UserResources)
    name = models.CharField(max_length=200)
    locusType = models.IntegerField(null=True,blank=True,max_length=1,verbose_name='type')
    forwardPrimer = models.CharField(max_length=200)
    reversePrimer = models.CharField(max_length=200)
    #For backwards compatibility following fields are all null=True,blank=True as they were not in previous versions
    refnumber = models.FloatField(null=True,blank=True,verbose_name='reference repeat number') #For STR loci alleles #TODO add validator
    refsequence = models.CharField(null=True,blank=True,max_length=1000) 
    refmask = models.CharField(null=True,blank=True,max_length=1000) #TODO add validator same length as refsequence
    
    class Meta:
        unique_together = ("configuration", "name")
        ordering = ('name',)
    
    def __str__(self):
        return self.name
        
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
    flankOut = models.BooleanField(default=False,help_text=mark_safe(
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

    class Meta:
        ordering = ['-creationTime']

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
#Previous lambda functions that needed to be named for migrations to work
def xmlUpload(instance,filename): return st('resultfiles/%Y/%m/%d/')+instance.analysis.configuration.fulldbname()+'.xml'
def pngUpload(instance,filename): return st('resultfiles/%Y/%m/%d/')+instance.analysis.configuration.fulldbname()+'.png'
class AnalysisResults(models.Model):
    """
    One-to one linked with analysis. Info for post-processing.
    The first time xmlFile gets modified after analysis, 
    original file should be copied to xmlOriginalFile
    """
    analysis = models.OneToOneField(Analysis)
    xmlFile = models.FileField(upload_to=xmlUpload)
    xmlOriginalFile = models.FileField(null=True,upload_to=xmlUpload)
    figFile = models.ImageField(upload_to=pngUpload)

    def updateXML(self,xmlroi,allele,locus=None):
        """
        Updates xmlFile if alleles are added from result page.
        Original file is always kept, but currently not available for users.
        However the original image does not change, so that can be used to compare
        the current state of the xml file to its original analysis.
        Returns True on success, False if no match to replace was found.
        """
        if not self.xmlOriginalFile:
            self.xmlOriginalFile = self.xmlFile
            self.xmlOriginalFile.file.open()
            self.xmlFile = self.xmlOriginalFile.file
            self.save()
        if not locus: locus = allele.locus

        #Update allele in file
        import xml.etree.ElementTree as ET
        tree = ET.parse(self.xmlFile.file.name)
        root = tree.getroot()
        for a in root.findall('locus[@name="{}"]/alleleCandidate'.format(
                locus)):
            if a.find('regionOfInterest').text == xmlroi:
                a.set('db-name',allele.FLADid)
                tree.write(self.xmlFile.file.name)
                #Prepare file for write out
                #Copy previous processing instructions
                procins = b''
                with open(self.xmlFile.file.name,'rb') as xmlFile:
                    for line in xmlFile:
                        if line.startswith(b'<?'): procins+=line
                        else: break
                with open(self.xmlFile.file.name,'wb') as xmlFile:
                    xmlFile.write(procins)
                    tree.write(xmlFile)
                return True
        return False



#Alleledatabase
class Allele(models.Model):
    """
    This model lists all alleles analyzed per user configuration
    """
    configuration = models.ForeignKey(UserResources)
    locus = models.ForeignKey(Locus)
    name = models.CharField(default='NA',max_length=200)
    FLADid = models.CharField(default='FAXXX',max_length=200) #TODO FLAD validator
    isFLAD = models.BooleanField(default=True) #True for validated alleles with a FLAdid
    repeatNumber = models.FloatField(null=True,blank=True,verbose_name='repeat number') #For STR loci alleles
    sequence = models.CharField(max_length=1000,default='')
    analysis = models.ForeignKey(Analysis,related_name='first_reporting_analysis',null=True,
                                 blank=True) #Alleles from original csv file will not be linked to an analysis
    reports = models.ManyToManyField(Analysis) #All analysis in which allele is reported
    initialPopstat = models.FloatField(null=True,blank=True,verbose_name='initial population statistic')
    popstat = models.FloatField(null=True,verbose_name='population statistic') #Calculated popstat based on reports
    timeAdded = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("configuration", "locus", "FLADid")
        ordering = ('locus',)
    
    def __str__(self):
        return self.FLADid

    @staticmethod
    def NAreference(locus,configuration=False):
        """
        Returns the first available NAreference for the configuration and locus.
        NAreferences are not permanent like a FLADid.
        If an NA allele gets validated and is assigned a FLADid,
        its NAreference is freed and used for the next NA allele that
        needs a reference.
        It is therefore important that users do not make too many profiles
        with NA alleles. Either an NA allele is valid and should get a FLADid,
        or it is not and it should be removed from the profile.

        If you provide configuration, locusName is sufficient.
        """
        if not type(locus) == Locus:
            locus = Locus.objects.get(configuration=configuration,
                                      name=locus)
        NAr = 0
        NAre = re.compile(r'NA(?P<number>\d+)')
        for i in sorted(int(NAre.match(a.FLADid).group('number'))
                      for a in Allele.objects.filter(locus=locus,isFLAD=False)):
            if i-1 == NAr:
                NAr +=1
            else: break
        NAr +=1
        return 'NA{}'.format(NAr)

    def NArelative(self,maxDifferences=2):
        """
        Searches the current configuration validated alleles
        and returns its NAreference_relativeFLADid+transformCode
        """
        return NotImplemented

class Profile(models.Model):
    """
    Collects all the alleles from an Analysis result that have been validated
    part of the profile.
    Non validated alleles can be part of a Profile, but it is not considered
    good practise. Profiles containing NA alleles should be reviewed.

    Profile.addToDatabase, adds all its alleles to the allele database and
    sets inAlleleDatabase to True. Profile.removeFromDatabase does the opposite.

    Profiles with NA alleles cannot be added to an allele config database.
    """
    analysis = models.OneToOneField(Analysis)
    alleles = models.ManyToManyField(Allele)
    threshold = models.FloatField(default=0,help_text=
                'Threshold applied when profile was generated from resultxml'
    )
    inAlleleDatabase = models.BooleanField(default=False) #True if used for allele DB

    def __str__(self):
        return 'Profile {}'.format(self.analysis.id)

    def isValid(self):
        """
        Returns True if no NA alleles in the profile.
        """
        return not self.alleles.filter(isFLAD=False).exists()

    def updateAlleles(self,alleles):
        """
        alleles => set of Allele objects
        """
        if self.alleles.all().exists() and self.inAlleleDatabase:
            #A changed profile has to be revalidated to be in popstat db
            self.removeFromDatabase()
            
        toRemove = set(self.alleles.all()) - alleles
        self.alleles.remove(*toRemove)
        self.alleles.add(*alleles)

    def as_table(self):
        """
        Makes a list of lists suitable for an html table representation
        E.g.:
        locus1 a1 a2
        locus2 a1
        ...
        """
        tableList = []
        alleles = (a for a in self.alleles.all())
        allele = next(alleles)
        for l in self.analysis.configuration.locus_set.all():
            tableList.append([l.name])
            try:
                while allele.locus == l:
                    tableList[-1].append(allele)
                    allele = next(alleles)
            except StopIteration: continue
        return tableList

    def toggleDB(self):
        if self.inAlleleDatabase: self.removeFromDatabase()
        else: self.addToDatabase()
    
    def addToDatabase(self):
        for a in self.alleles.all():
            a.reports.add(self.analysis)
        self.inAlleleDatabase = True

    def removeFromDatabase(self):
        for a in self.alleles.all():
            a.reports.remove(self.analysis)
        self.inAlleleDatabase = False
    
class FLADconfig(models.Model):
    """
    Username and registration key on forensic.UGent.be.
    This is defined in the 'myflq' app instead of the 'flad' 
    app for compatibility with standalone MyFLq installations.
    """
    user = models.OneToOneField(User) #only one FLADconfig per user
    FLAD = models.CharField(max_length=200,default='forensic.ugent.be',
                            verbose_name='FLADprovider',help_text='Domain name for your FLAD provider. E.g. forensic.ugent.be')
    FLADname = models.CharField(max_length=30) #30 maximum Django username length
    FLADkey = models.CharField(max_length=50)  #50 => no need to exagerate
