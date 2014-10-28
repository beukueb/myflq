from django import forms
from django.forms.formsets import formset_factory

class RForm(forms.Form):
    locus = forms.CharField(help_text="Locus name",required=False)
    allele = forms.CharField(help_text="Allele number/name")
    frequency = forms.FloatField(help_text="Population frequency (between 0 and 1)")
    observed = forms.BooleanField(help_text="Check if allele observed in profile",
                                  widget=forms.CheckboxInput(attrs={'class':'cbox'}),
                                  required=False
    )

RFormSet = formset_factory(RForm, extra=10)

class SettingsFileForm(forms.Form):
    fileName = forms.FileField(label="File with population frequencies")
