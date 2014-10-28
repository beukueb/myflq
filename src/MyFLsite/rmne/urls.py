from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required#, permission_required
from django.views.generic import TemplateView

urlpatterns = patterns('',
    #All keys in kwargs need to be strings, with TemplateView they are passed to the context
    url(r'^$', 'rmne.views.calcform'), 
    #url(r'^help/$', login_required(TemplateView.as_view(template_name='myflq/help.html')),kwargs={'myflq':True}), 
)
