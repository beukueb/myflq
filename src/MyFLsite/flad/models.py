from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.exceptions import ObjectDoesNotExist
import re

class Locus(models.Model):
    """
    Different loci that are used in Allele
    """
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Allele(models.Model):
    """
    This is the model for the Forensic Loci Allele Database aka FLAD.
    Only on the FLAD server should testing be set to true.
    """
    fladid = models.PositiveIntegerField(verbose_name='FLADid',null=True)
    locus = models.ForeignKey(Locus,null=True)
    sequence = models.TextField(max_length=1000,verbose_name="allele sequence",
                                help_text='Allele sequence should only contain A,C,T or G, and N for masked bases',
                                validators=[RegexValidator(regex=r'^[ACTGN]*$', message='Should ony contain nucleotide letters A,C,T, or G, and N for masked bases.')])
    length = models.PositiveIntegerField()    
    users = models.ManyToManyField(User)
    creationDate = models.DateField(auto_now_add=True)
    validation = models.NullBooleanField(default=False) #Set to None for deleted alleles
    validationUser = models.ForeignKey(User,null=True,related_name="vuser")
    doi = models.CharField(max_length=200,null=True) #If validated, doi for validation pubblication

    #Class attributes
    context = 'L' # 'T' for testing, 'L' for local and 'F' for FLAD on ugent.be
        #todo change LF to F on forensic.ugent.be
    fladrex = re.compile(r'(?P<context>[FLT])(L(?P<locus>\d+))?' +
                         r'(?P<valid>[AX])(?P<fladid>[\dA-F]{2,})' +
                         r'(?P<transform>t[oc]((\d+)(((\.\d+)?[ACTGNd])+)(i?))*)?$')
    doirex = re.compile(r'\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?!["&\'<>])\S)+)\b')

    def save(self, *args, **kwargs):
        self.length = len(self.sequence)
        return super(Allele, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.getfladid()

    def getfladid(self):
        """
        This is the FLADid for the sequence
        A FLADid from forensic.ugent.be starts with 'F'
        On a local running FLADid provider this will start with 'LF'
        A FLAXid for testing starts with 'TF'
        """
        if not self.fladid: return None
        
        #Returns an uppercase hex id
        fladstring = '{context}{locus}{valid}{fladid:0>3X}{transformcode}'
        if self.locus: fladstring = fladstring.replace('>3X','>2X')
        return fladstring.format(
            context = self.context,
            locus = 'L{}'.format(self.locus_id) if self.locus else '',
            valid = 'A' if self.validation else 'X',
            fladid = self.fladid,
            transformcode = self.transformCode if hasattr(
                self,'transformCode') else ''
        )

    def transform(self,transformCode):
        """
        Transforms the sequence of the FLAD allele according to the
        transformCode.
        The transformCode is the FLAD version, and has to start with
        either 'to' or 'tc' to indicate which strand needs to be transformed

        Returns the transformed sequence.
        However if the exact sequence is already in the database, an StopIteration
        exception is raised.
        """
        from myflq.MyFLq import complement, Alignment
        cls = type(self)
        self.transformCode = transformCode
        if transformCode.startswith('tc'): seq=complement(self.sequence)
        else: seq = self.sequence
        if len(transformCode) > 2:
            transformCode = 't'+transformCode[2:]
            seq = Alignment.transformSeq(transformCode,seq)
            
        #Test if exact transformed sequence is in database
        if self.transformCode in ('tc','to'):
            if self.transformCode == 'to': del self.transformCode
            return seq
        try:
            allele = cls.search(seq,seqid=True)
            if allele.sequence != seq:
                allele.transformCode = 'tc'
            raise StopIteration(allele)
        except ObjectDoesNotExist: return seq

    def getsequence(self):
        """
        Returns sequence, accounting for transformCode if necessary.
        If you are not sure that a transformCode could be present,
        it is better to use self.getseq() instead of self.sequence
        """
        if hasattr(self,'transformCode'): return self.transform(self.transformCode)
        else: return self.sequence
    getseq = getsequence #abbreviation for backwards compatibility

    def getcomplement(self):
        """
        Returns the complement sequence
        uses getseq, so if their is a transformCode it will be applied.
        """
        from myflq.MyFLq import complement
        return complement(self.getseq())

    def validate(self,user,doi):
        """
        If not validated, adds the doi and sends a message that the validation
        needs to be checked. Only then should validation be set to true.
        In the future this should be automated by text mining the doi, and
        checking if the allele sequence is linked to the pubblication.
        Returns True if adding doi succesful, False if already has a doi linked
        or some other issue.
        """
        if self.doi: return False
        else:
            #Check doi format
            match = self.doirex.search(doi)
            if not match: raise KeyError('Wrong format: {}'.format(doi))
            doi = match.group()

            #Check if active doi
            url = 'http://dx.doi.org/{doi}'.format(doi=doi)
            ##Curl
            #import pycurl
            #from io import BytesIO
            #buffer = BytesIO()
            #c = pycurl.Curl()
            #c.setopt(c.URL,url)
            #c.setopt(c.WRITEDATA, buffer)
            #c.setopt(c.HTTPHEADER, ['Accept: application/rdf+xml'])
            #c.perform()
            #c.close()
            #response = buffer.getvalue()
            
            ##urllib
            from urllib import request
            import socket
            #If original browser link is needed, add user_Agent to headers
            #user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
            headers = {'Accept':'application/rdf+xml'}
                      #'User-Agent':user_agent,
                      #'Accept':'text/turtle' => would then require rdflib for parsing
            req = request.Request(url, headers = headers)
            userName = '{} {}'.format(user.userprofile.firstname,
                                      user.userprofile.lastname)
            try:
                try:
                    response = request.urlopen(req)
                    #Check if user is author of the referenced pubblication
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.read())
                    root = root.getchildren()[0]
                    namespaces={'j.2':'http://purl.org/dc/terms/',
                                'j.1':'http://xmlns.com/foaf/0.1/'}
                    for c in root.findall('j.2:creator',namespaces=namespaces):
                        name = c.find('j.1:Person/j.1:name',namespaces=namespaces)
                        name = name.text
                        if name == userName:
                            raise StopIteration
                except request.HTTPError: raise
                except (request.URLError,socket.gaierror):
                    #In case of timeout, use crossref site instead of doi
                    url = 'http://search.crossref.org/dois?q={doi}'.format(doi=doi)
                    response = request.urlopen(url)
                    #Check if user is author of the referenced pubblication
                    import json
                    data = json.loads(response.read().decode())
                    if not data: raise request.HTTPError #No results
                    if userName in data[0]['fullCitation']:
                        raise StopIteration
                
                #user is not an author => log
                import logging
                logger = logging.getLogger(__name__)
                logger.info('User {} requests validation of {}, with doi {}.'.format(
                    user,self,doi))
                raise KeyError('User {} not an author of {}'.format(user,doi))
            except request.HTTPError: raise KeyError('doi {} not valid'.format(doi))
            except StopIteration:
                #user is author
                self.doi = doi
                self.validationUser = user
                self.validation = True
                self.save()
                return True
            
    @classmethod
    def add(cls,sequence,locus=None,user=None):
        """
        Adds a locus/sequence to FLAD
        Works like get_or_create, but only returns the Allele object
        """
        from myflq.MyFLq import complement
        if locus: locus = Locus.objects.get_or_create(name=locus.upper())[0]
        #Last check to see if complement is not in database
        assert not cls.objects.filter(sequence=complement(sequence),
                                      locus=locus).exists()
        allele,crtd = cls.objects.get_or_create(sequence=sequence,locus=locus)
        if crtd: #if created
            allelePosition = list(cls.objects.filter(locus=locus)).index(allele)
            if not locus: randomSampleSpace = 1000
            else: randomSampleSpace = 100
            alleleBin = int(allelePosition/randomSampleSpace)*randomSampleSpace
            allelePosition = allelePosition % randomSampleSpace
            alleleChoices = list(range(alleleBin+1,alleleBin+randomSampleSpace+1))
            import random
            random.seed(str(locus)+str(alleleBin))
            random.shuffle(alleleChoices)
            allele.fladid = alleleChoices[allelePosition]
            allele.save()
        #In case already added, just add user
        if user: allele.users.add(user)
        return allele
        
        
    @classmethod
    def search(cls,fladid=False,locus=None,seq=False,closeMatch=False):
        """
        Searches for an allele, either with a FLADid or a locus/sequence combo
        In case of a locus/sequence, if no exact match is found, it will
        look for any close match up to 10 difference
        If looking up a sequence, with closeMatch, similar sequences
        will also be considered. Their FLADid will then be returned with
        transformCode.
        """
        from myflq.MyFLq import complement
        if fladid:
            match = cls.fladrex.match(fladid)
            fladid = int(match.group('fladid'),base=16)
            locus = match.group('locus')
            if locus: locus = Locus.objects.get(id=locus)
            allele = cls.objects.get(fladid=fladid,
                                     locus=locus)
        else:
            if locus: locus = Locus.objects.get_or_create(name=locus.upper())[0]
            try: allele = cls.objects.get(sequence=seq,locus=locus)
            except ObjectDoesNotExist:
                try:
                    allele = cls.objects.get(sequence=complement(seq),
                                             locus=locus)
                    allele.transformCode = 'tc'
                except ObjectDoesNotExist:
                    if closeMatch:
                        allele = cls.closeMatch(sequence=seq,
                                                locus=locus,
                                                differences=10)
                    else: raise
        return allele

    @classmethod
    def closeMatch(cls,sequence,differences=10,minimalKmerSize=5):
        """
        Searches if there exists a close match with a maximum number
        of differences that can be provided as argument.
        It uses a heuristic that if fast, but could miss some matches,
        notwithstanding that there are less than the differences allowed.

        Returns the matching allele, with transformCode attribute.
        If no match is found raises ObjectDoesNotExist
        """
        from myflq.MyFLq import complement, Alignment
        
        #First filter based on length
        seqlen = len(sequence)
        alleles = cls.objects.filter(length__gt=(0 if seqlen < differences
                                       else seqlen-differences)).filter(
                                               length__lt = seqlen+differences)
        alleles = {a:[0,0] for a in alleles}
        
        #Filter based on kmer from sequence
        if seqlen > minimalKmerSize:
            kmersize = int(seqlen/(differences+1))
            if kmersize < minimalKmerSize: kmersize = minimalKmerSize
            kmers = {sequence[i:i+kmersize]
                     for i in range(0,seqlen-kmersize,kmersize)}
            kmers_c = {complement(k) for k in kmers}
            for a in alleles:
                for k in kmers:
                    if k in a.sequence: alleles[a][0]+=1
                for k in kmers_c:
                    if k in a.sequence: alleles[a][1]+=1
            alleles = {a:alleles[a] for a in alleles if sum(alleles[a])}

        #Look for match that meets differences requirement
        matchedAllele = None
        for allele in sorted(alleles,key=lambda x: max(alleles[x]),reverse=True):
            complementary = alleles[allele][0] < alleles[allele][1]
            alignment = Alignment(allele.sequence,sequence #Without stutter info for now #TODO
                                  if not complementary else complement(sequence),
                                  gapPenalty=-10,gapExtension=-5)
            if alignment.getDifferences() <= differences:
                tc = alignment.getTransformCode(startSequence=allele.sequence)
                tc = ('tc' if complementary else 'to')+tc[1:]
                allele.transformCode = tc
                if not matchedAllele or len(matchedAllele.transformCode) > len(tc):
                    matchedAllele = allele
                #If difference in k-mer count is already substantial => break
                elif max(alleles[matchedAllele]) > max(alleles[allele])+2: break
        if matchedAllele: return matchedAllele
        else: raise ObjectDoesNotExist

    @classmethod
    def checkIntegrity(cls):
        """
        Checks if everything has unique ID per locus
        This function should be used in a weekly/monthly test
        Unicity cannot be garanteed on the model level, as ID are assigned
        after creation to avoid race conditions.
        The algorithm that then assigns a random number with seed should
        produce the same random and unique number for an allele added.
        Alleles should not be allowed to be removed, otherwise it will break this logic.
        """
        raise NotImplemtedError

    def delete(self,trulyDelete=False):
        """
        This reimplements the delete method as alleles cannot truly be deleted.
        Their sequence is replaced with '' and validation to None.

        trulyDelete deletes it for real. Only use it if you understand the above
        implications. Should not be done on forensic.ugent.be/FLAD, but only
        on a local running service to reset.
        """
        if not trulyDelete:
            self.sequence = ''
            self.validation = None
            self.save()
        else: super(type(self),self).delete()

class TestAllele(Allele):
    """
    This model will be used by the FLAD testing service FLAX
    """
    context = 'T'

class FLADkey(models.Model):
    """
    Registration key for forensic.UGent.be.
    """
    user = models.OneToOneField(User) #only one FLADconfig per user
    FLADkey = models.CharField(max_length=50)  #50 => no need to exagerate
