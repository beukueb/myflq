from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required#, permission_required
from django.views.generic import TemplateView

urlpatterns = patterns('',
    #All keys in kwargs need to be strings, with TemplateView they are passed to the context
    url(r'^$', TemplateView.as_view(template_name='flad/home.html'),kwargs={'flad':True}),
    url(r'^query/$', TemplateView.as_view(template_name='flad/base.html'),kwargs={'flad':True}),                        
    url(r'^sequence/(?P<xml>xml/|)(?P<fladid>FA\w*)/$','flad.views.getsequence'),
    url(r'^getid/(?P<xml>xml/|)(?P<seq>[ACTGN]*)$','flad.views.getid'),
    url(r'^addid/(?P<xml>xml/|)(?P<seq>[ACTGN]*)$','flad.views.addid'),
)
