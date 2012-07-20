from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('builder.views',
    # Examples:
    # url(r'^$', 'memebuilder.views.home', name='home'),
    # url(r'^memebuilder/', include('memebuilder.foo.urls')),
    url(r'^$', 'index'),
    url(r'caption/(?P<fn>\w+.\w+)/$', 'caption', name='caption'),
    url(r'thumbnail/(?P<fn>\w+.\w+)/$', 'thumbnail', name='thumbnail'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
