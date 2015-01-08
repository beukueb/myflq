
# Create your views here.

from django.shortcuts import render,render_to_response
from django.http import HttpResponseRedirect
from django import forms
from django.contrib.auth.forms import UserCreationForm
from main.forms import ContactForm, UserProfileForm

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        pform = UserProfileForm(request.POST)
        if form.is_valid() and pform.is_valid():
            import logging
            logger = logging.getLogger('django.request')
            logger.info('New registered user\n'+str(request).replace('\n','\n\t'))
            new_user = form.save()
            pform.instance.user = new_user
            pform.save()
            return HttpResponseRedirect("/")
    else:
        form = UserCreationForm()
        pform = UserProfileForm()
    return render(request, "registration/register.html", {
        'form': form,
        'pform': pform,
    })


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            topic = form.cleaned_data['topic']
            message = form.cleaned_data['message']
            sender = form.cleaned_data.get('sender', 'noreply@example.com')

            from django.core.mail import send_mail
            send_mail(
                'Feedback from your site, topic: {}'.format(topic),
                message, sender,
                ['christophe.vanneste@ugent.be']
            )
            return HttpResponseRedirect('/contact/thanks/')
    else:
        form = ContactForm()
    return render(request,'main/contact.html', {'form': form,
                                                'widgets': [{'img':'images/contact.png','style':'margin-top:50px;'}]})

