from django.conf.urls.defaults import patterns, include, url
from packages.views import details

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from django.conf import settings
import os.path

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'packages_pardus.views.home', name='home'),
    # url(r'^packages_pardus/', include('packages_pardus.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^packages/', include('packages.urls')),
)

if settings.DEBUG == True:
    urlpatterns += patterns('',
        (r'^media/(.*)$', 'django.views.static.serve',{'document_root':
                                               os.path.join(settings.DEPLOY_PATH, 'media')}), 
                            (r'^jsi18n/$',   'django.views.i18n.null_javascript_catalog'), )
