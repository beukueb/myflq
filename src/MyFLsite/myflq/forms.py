from django import forms
from django.forms import ModelForm
from django.forms.models import modelformset_factory

from myflq.models import Primer, AlleleFiles, Analysis

#Primers
def primerformset_factory(queryset):
    class PrimerForm(ModelForm):
        dbname = forms.ModelChoiceField(queryset)
        class Meta:
            model = Primer
            fields = ['dbname', 'locusName', 'locusType', 'forwardPrimer', 'reversePrimer']
            widgets = { 'locusName': forms.TextInput(attrs={'size':'5'}),
                        'locusType': forms.TextInput(attrs={'size':'5','maxlength':'2'}), #when browsers support should be: forms.NumberInput(attrs={'max':'10'})
                        'forwardPrimer': forms.TextInput(attrs={'size':'10'}),
                        'reversePrimer': forms.TextInput(attrs={'size':'10'}) }
            
    PrimerFormSet = modelformset_factory(Primer,PrimerForm,extra=3,can_delete=True)
                #Can also be defined without PrimerForm, including => fields = ['dbname',...],widgets = { 'locusName':forms.Textarea(),'locusType': forms.NumberInput(attrs={'size':'5'}) } )
    return PrimerFormSet

def primerfileform_factory(queryset):
    class PrimerFileForm(forms.Form):
        dbname = forms.ModelChoiceField(queryset)
        fileName = forms.FileField(label="File with loci info")
        
        def clean_fileName(self):
            locifile = self.cleaned_data.get('fileName',False)
            if locifile:
                if locifile.size > 5*1024*1024:
                    raise forms.ValidationError("Loci file too large ( > 5 MB )")
                return locifile
            else:
                raise forms.ValidationError("Couldn't read uploaded file")
    return PrimerFileForm
        
        #Apache configuration:  !!!
        #    Configure the Web server to limit the allowed upload body size. 
        #    e.g. if using Apache, set the LimitRequestBody setting. 
        #    This will mean if a user tries to upload too much, they'll get an error page configurable in Apache
        


#from django.forms.models import inlineformset_factory #=> to allow editing Primers for a specific UserResource database
#from myflq.models import UserResources
#PrimerFormSet = inlineformset_factory(UserResources, Primer,fields = ['dbname', 'locusName', 'locusType', 'forwardPrimer', 'reversePrimer'])


#Alleles
def allelefileform_factory(queryset):
    class AlleleFileForm(ModelForm):
        dbname = forms.ModelChoiceField(queryset)
        #fileName = forms.FileField(label="File with loci info")
        
        class Meta:
            model = AlleleFiles
            fields = ['dbname','alleleFile']
        def clean_alleleFile(self):
            afile = self.cleaned_data.get('alleleFile',False)
            if afile:
                if afile.size > 5*1024*1024:
                    raise forms.ValidationError("Allele file too large ( > 5 MB )")
                return afile
            else:
                raise forms.ValidationError("Couldn't read uploaded file")
    return AlleleFileForm

def databaseselectionform_factory(queryset):
    from myflq.models import Primer,AlleleFiles
    class DatabaseSelectionForm(forms.Form):
        dbname = forms.ModelChoiceField(queryset)
        
        def clean_dbname(self):
            dbname = self.cleaned_data.get('dbname',False)
            if dbname:
                if dbname.isAlreadyCommitted:
                    raise forms.ValidationError(dbname.dbname+' has already been committed!'+
                                                 ' If you want to use same database name, delete database and restart.')
                elif not Primer.objects.filter(dbname=dbname).exists():
                    raise forms.ValidationError(dbname.dbname+' has no primers linked. First add primers!')
                elif not AlleleFiles.objects.filter(dbname=dbname).exists():
                    raise forms.ValidationError(dbname.dbname+' has no uploaded allele file. First upload allele file!')
                return dbname
            else: raise forms.ValidationError("Couldn't read uploaded file")
        
    return DatabaseSelectionForm

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
