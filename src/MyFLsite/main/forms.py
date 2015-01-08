from django import forms
from django.forms import ModelForm

TOPIC_CHOICES = (
    ('general', 'General enquiry'),
    ('bug', 'Bug report'),
    ('suggestion', 'Suggestion'),
)

class ContactForm(forms.Form):
    topic = forms.ChoiceField(choices=TOPIC_CHOICES)
    message = forms.CharField(widget=forms.Textarea())
    sender = forms.EmailField(required=False)

from main.models import UserProfile
class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        exclude = ['user','fladPriviliged']
