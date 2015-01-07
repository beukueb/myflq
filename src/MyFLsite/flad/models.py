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
    users = models.ManyToManyField(User)
    creationDate = models.DateField(auto_now_add=True)
    testing = False

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
        return ('FX' if self.testing
                else 'FL')+'{:0>3X}'.format(self.id) #Returns an uppercase hex id

    def transform(self,transformCode):
        """
        Transforms the sequence of the FLAD allele according to the
        transformCode.
        The transformCode is the FLAD version, and has to start with
        either 'to' or 'tc' to indicate which strand needs to be transformed

        Returns the transformed sequence
        """
        from myflq.MyFLq import complement, Alignment
        if transformCode.startswith('tc'): seq=complement(self.sequence)
        else: seq = self.sequence
        if len(transformCode) > 2:
            transformCode = 't'+transformCode[2:]
            seq = Alignment.transformSeq(transformCode,seq)
        return seq
        
    @classmethod
    def search(cls,id,seqid=False):
        """
        Searches for an allele, either with a FLADid or a sequence
        """
        if seqid:
            try: allele = cls.objects.get(sequence=id)
            except ObjectDoesNotExist:
                allele = cls.objects.get(sequence=id)
        else: allele = cls.objects.get(id=int(id[2:],base=16))
        return allele 

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
