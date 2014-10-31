from django import forms
from django.forms import ModelForm
from django.forms.models import modelformset_factory

from myflq.models import UserResources,Analysis

#Setup
from django.core.validators import RegexValidator
class ConfigurationForm(ModelForm):
    class Meta:
        model = UserResources
        exclude = ['user','creationDate']
        widgets = {
            'description': forms.Textarea(attrs={'rows':2, 'cols':50}),
        }
        
    def clean_lociFile(self):
        locifile = self.cleaned_data.get('lociFile',False)
        if locifile:
            if locifile.size > 5*1024*1024:
                raise forms.ValidationError("Loci file too large ( > 5 MB )")
            return locifile
        else:
            raise forms.ValidationError("Couldn't read uploaded file")

    def clean_alleleFile(self):
        afile = self.cleaned_data.get('alleleFile',False)
        if afile:
            if afile.size > 5*1024*1024:
                raise forms.ValidationError("Allele file too large ( > 5 MB )")
            return afile
        else:
            raise forms.ValidationError("Couldn't read uploaded file")        
    #Webserver configuration:  !!!
    #    Configure the Web server to limit the allowed upload body size. 
    #    e.g. if using Apache, set the LimitRequestBody setting. 
    #    This will mean if a user tries to upload too much, they'll get an error page configurable in Apache
        

#Analysis
class FastqChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.originalFilename

def analysisform_factory(db_queryset,upfiles_queryset):
    uniqueUpFiles = {up['originalFilename']:up['id'] for up in upfiles_queryset.values('id','originalFilename')}.values()
    class AnalysisForm(ModelForm):
        dbname = forms.ModelChoiceField(db_queryset)
        prevUploadedFiles = FastqChoiceField(upfiles_queryset.filter(id__in=uniqueUpFiles),required=False,empty_label="(Upload file instead)")
        
        class Meta:
            model = Analysis
            exclude = ['originalFilename','progress','creationTime']
        
        def clean_dbname(self):
            dbname = self.cleaned_data.get('dbname',False)
            if dbname:
                if not dbname.isAlreadyCommitted:
                    raise forms.ValidationError(dbname.dbname+' has not yet been committed!'+
                                                 ' If you want to use this database for analysis, commit it first in Setup.')
                return dbname
            else: raise forms.ValidationError("Dbname not provided")

        #def clean_fastq(self): #when cleaning needs to combine different form fields
        # do that from general 'clean' method
        def clean(self):
            fastq = self.cleaned_data.get('fastq',False)
            if not fastq:
                prevUploadedFile = self.cleaned_data.get('prevUploadedFiles',False)
                if prevUploadedFile:
                    self.cleaned_data['fastq'] = prevUploadedFile.fastq
                    self.cleaned_data['originalFilename'] = prevUploadedFile.originalFilename
                else: raise forms.ValidationError('No FASTQ provided.')
            #return fastq
            return self.cleaned_data
        
    return AnalysisForm
