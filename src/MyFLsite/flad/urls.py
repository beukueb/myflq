from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required#, permission_required
from django.views.generic import TemplateView

urlpatterns = patterns('',
    #All keys in kwargs need to be strings, with TemplateView they are passed to the context
    url(r'^$', TemplateView.as_view(template_name='flad/home.html'),kwargs={'flad':True}),
    url(r'^query/$', TemplateView.as_view(template_name='flad/base.html'),kwargs={'flad':True}),
    url(r'^testing/$', TemplateView.as_view(template_name='flad/testing.html'),kwargs={'flad':True}),
    url(r'^help/$', TemplateView.as_view(template_name='flad/help.html'),kwargs={'flad':True}),
    url(r'^registration/$','flad.views.registration'),
    url(r'^getseq/(?P<mode>xml/|plain/|)(?P<fladid>[FLT](L\d+)?[AX][\dA-F]{2,})'+
        r'(?P<transform>t[oc]((\d+)(((\.\d+)?[ACTGNd])+)(i?))*)?/$',
        'flad.views.getsequence'),
    url(r'^getid/(?P<mode>xml/|plain/|)(?P<validate>validate/|)((?P<locus>[a-zA-Z][-\w]+)/)?(?P<seq>[ACTGN]*)$','flad.views.getid'),
                       #for locus regex: first letter should be a letter, following symbols alphanumeric or '-'
    url(r'^(?P<message>.*)/$','flad.views.error'),
)
