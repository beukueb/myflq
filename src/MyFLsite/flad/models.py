from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.exceptions import ObjectDoesNotExist

class Allele(models.Model):
    """
    This is the model for the Forensic Loci Allele Database aka FLAD.
    Only on the FLAD server should testing be set to true.
    """
    id = models.PositiveIntegerField(verbose_name='FLADid',primary_key=True)
    sequence = models.TextField(max_length=1000,verbose_name="allele sequence",
                                help_text='Allele sequence should only contain A,C,T or G, and N for masked bases',
                                validators=[RegexValidator(regex=r'^[ACTGN]*$', message='Should ony contain nucleotide letters A,C,T, or G, and N for masked bases.')])
    length = models.PositiveIntegerField()    
    users = models.ManyToManyField(User)
    creationDate = models.DateField(auto_now_add=True)
    testing = False

    def save(self, *args, **kwargs):
        cls = type(self) #To make difference between Allele and TestAllele if necessary
        self.length = len(self.sequence)
        return super(cls, self).save(*args, **kwargs)
    
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
        return ('FX' if self.testing
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
    def search(cls,id,seqid=False):
        """
        Searches for an allele, either with a FLADid or a sequence
        In case of a sequence, if no exact match is found, it will
        look for any close match up to 10 difference
        """
        from myflq.MyFLq import complement
        if seqid:
            try: allele = cls.objects.get(sequence=id)
            except ObjectDoesNotExist:
                try: allele = cls.objects.get(sequence=complement(id))
                except ObjectDoesNotExist:
                    allele = cls.closeMatch(sequence=id,differences=10)
        else: allele = cls.objects.get(id=int(id[2:],base=16))
        return allele

    @classmethod
    def closeMatch(cls,sequence,differences=10):
        """
        Searches if there exists a close match with a maximum number
        of differences that can be provided as argument.
        It uses a heuristic that if fast, but could miss some matches,
        notwithstanding that there are less than the differences allowed.

        Returns the matching allele, with transformCode attribute.
        If no match is found raises ObjectDoesNotExist
        """
        
        raise ObjectDoesNotExist

class TestAllele(Allele):
    """
    This model will be used by the FLAD testing service FLAX
    """
    testing = True

class UsableReference(models.Model):
    """
    If an allele is deleted from FLAD, its id is collected here for random reuse
    """
    id = models.PositiveIntegerField(primary_key=True)

class FLADkey(models.Model):
    """
    Registration key for forensic.UGent.be.
    """
    user = models.OneToOneField(User) #only one FLADconfig per user
    FLADkey = models.CharField(max_length=50)  #50 => no need to exagerate
