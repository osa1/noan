from django.conf.urls.defaults import patterns, include, url
from packages.views import details

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'packages_pardus.views.home', name='home'),
    # url(r'^packages_pardus/', include('packages_pardus.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^packages/(?P<dist>[A-z0-9\-]+)/(?P<arch>[A-z0-9]+)/(?P<name>[A-z0-9\-+.]+)/', details),
)
