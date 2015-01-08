from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    """
    This model extends the user profile for registration.
    """
    user = models.OneToOneField(User)
    email = models.EmailField(max_length=254,verbose_name='email (*)')
    firstname = models.CharField(null=True,blank=True,max_length=200,
                                 verbose_name='first name')
    lastname = models.CharField(null=True,blank=True,max_length=200,
                                verbose_name='last name')    
    institute = models.CharField(null=True,blank=True,max_length=200,
                                 verbose_name='forensic institute/lab')
    fladRequest = models.BooleanField(default=False,verbose_name='request FLAD validation')
    fladPriviliged = models.BooleanField(default=False)

    def __str__(self):
        return 'Profile {}'.format(self.user)
