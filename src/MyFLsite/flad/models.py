from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.exceptions import ObjectDoesNotExist

class Locus(models.Model):
    """
    Different loci that are used in Allele
    """
    name = models.CharField(max_length=100)
    
class Allele(models.Model):
    """
    This is the model for the Forensic Loci Allele Database aka FLAD.
    Only on the FLAD server should testing be set to true.
    """
    fladid = models.PositiveIntegerField(verbose_name='FLADid')
    locus = models.ForeignKey(Locus)
    sequence = models.TextField(max_length=1000,verbose_name="allele sequence",
                                help_text='Allele sequence should only contain A,C,T or G, and N for masked bases',
                                validators=[RegexValidator(regex=r'^[ACTGN]*$', message='Should ony contain nucleotide letters A,C,T, or G, and N for masked bases.')])
    length = models.PositiveIntegerField()    
    users = models.ManyToManyField(User)
    creationDate = models.DateField(auto_now_add=True)
    validation = models.NullBooleanField(default=False) #Set to None for deleted alleles
    doi = models.CharField(max_length=200,null=True) #If validated, doi for validation pubblication
    context = 'FLAD' # 'testing', 'local' or 'FLAD'

    def save(self, *args, **kwargs):
        self.length = len(self.sequence)
        return super(Allele, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.fladid()

    def fladid(self):
        """
        This is the FLADid for the sequence
        On a local running FLADid provider this will start with 'FL'
        A FLADid from forensic.ugent.be starts with 'FA'
        A FLAXid for testing starts with 'FX'
        """
        #todo change FL to FA on forensic.ugent.be
        #Returns an uppercase hex id
        return ('FX' if self.context == 'testing'
                else 'FL')+'{:0>3X}'.format(self.id) + (self.transformCode
                                    if hasattr(self,'transformCode') else '')

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

    def getseq(self):
        """
        Returns sequence, accounting for transformCode if necessary.
        If you are not sure that a transformCode could be present,
        it is better to use self.getseq() instead of self.sequence
        """
        if hasattr(self,'transformCode'): return self.transform(self.transformCode)
        else: return self.sequence
        
    @classmethod
    def search(cls,id,seqid=False,closeMatch=False):
        """
        Searches for an allele, either with a FLADid or a sequence
        In case of a sequence, if no exact match is found, it will
        look for any close match up to 10 difference
        If looking up a sequence, with closeMatch, similar sequences
        will also be considered. Their FLADid will then be returned with
        transformCode.
        """
        from myflq.MyFLq import complement
        if seqid:
            try: allele = cls.objects.get(sequence=id)
            except ObjectDoesNotExist:
                try:
                    allele = cls.objects.get(sequence=complement(id))
                    allele.transformCode = 'tc'
                except ObjectDoesNotExist:
                    if closeMatch:
                        allele = cls.closeMatch(sequence=id,differences=10)
                    else: raise
        else: allele = cls.objects.get(id=int(id[2:],base=16))
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
    context = 'testing'

class FLADkey(models.Model):
    """
    Registration key for forensic.UGent.be.
    """
    user = models.OneToOneField(User) #only one FLADconfig per user
    FLADkey = models.CharField(max_length=50)  #50 => no need to exagerate
