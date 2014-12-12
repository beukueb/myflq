from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
class Allele(models.Model):
    """
    This is the model for the Forensic Loci Allele Database aka FLAD.
    """
    id = models.PositiveIntegerField(verbose_name='FLADid',primary_key=True)
    sequence = models.TextField(max_length=1000,verbose_name="allele sequence",
                                help_text='Allele sequence should only contain A,C,T or G, and N for masked bases',
                                validators=[RegexValidator(regex=r'^[ACTGN]*$', message='Should ony contain nucleotide letters A,C,T, or G, and N for masked bases.')])
    users = models.ManyToManyField(User)
    creationDate = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.fladid()
        
    def fladid(self):
        """
        This is the FLADid for the sequence 
        """
        return 'FA{:0>3X}'.format(self.id) #Returns an uppercase hex id

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
