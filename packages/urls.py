from django.conf.urls.defaults import patterns, url
from packages.views import details, search


urlpatterns = patterns('',
        url(r'^$', search),
        url(r'^(?P<dist>[A-z0-9\-.]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/', details),
        url(r'^(?P<page>\d+)/$', search),
)
