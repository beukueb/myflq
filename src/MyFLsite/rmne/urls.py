from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required#, permission_required
from django.views.generic import TemplateView

urlpatterns = patterns('',
    #All keys in kwargs need to be strings, with TemplateView they are passed to the context
    url(r'^$', 'rmne.views.calcform'), 
    url(r'^help/$', TemplateView.as_view(template_name='rmne/help.html'),kwargs={'rmne':True}), 
)
