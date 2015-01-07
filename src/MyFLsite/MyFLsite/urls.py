from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login, logout
from django.views.generic import TemplateView
from django.conf.urls.static import static #DEBUG# Comment out on production server
from django.conf import settings #DEBUG# Currently only used for above debug line

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    #url(r'^$', 'MyFLsite.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    
    #General
                       url(r'^$', TemplateView.as_view(template_name='main/home.html'),
                           kwargs={'widgets':[
                               {'img':'images/LabFBTUGentlogo.png'},
                               {'img':'images/basespace-brand.png'},
                               {'img':'images/n2nLogo.png'},
                               #{'img':'images/ugentLogo.png'},
                               {'img':'images/MyFLqLogo.png'}]}),
    url(r'^source-files/$', TemplateView.as_view(template_name='main/sourcefiles.html')),
    url(r'^contact/$','main.views.contact'),
    url(r'^contact/thanks/$',TemplateView.as_view(template_name='main/thanks.html')),
                       url(r'^about/$', TemplateView.as_view(template_name='main/about.html'),
                           kwargs={'widgets':[
                               {'img':'images/group.png', 'caption':
'''MyFLq was developed by researchers at Ghent University's
Laboratory of Pharmaceutical Biotechnology and led by Professor
and Laboratory Director Dieter Deforce, Ph.D (middle), postdoctoral
researcher, Filip Van Nieuwerburgh, Ph.D. (right), and Ph.D. student
Christophe Van Neste (left).''','style':'border-radius:20px;'}
                           ]}),
    
    #Admin
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', login),
    url(r'^accounts/logout/$', logout),
    url(r'^register/$','main.views.register'),
    
    #MyFLq (only after login)
    url(r'^myflq/', include('myflq.urls')),
    url(r'^(?P<flad>flad|FLAD|flax|FLAX)/', include('flad.urls')),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) #DEBUG# Comment last line out on production server
