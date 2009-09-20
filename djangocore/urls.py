from django.conf.urls.defaults import *

from djangocore.handlers import length_resource, range_resource, bulk_resource, object_resource

urlpatterns = patterns('',
    url(r'^(?P<app_label>[^/]+)/(?P<module_name>[^/]+)/length/$', length_resource),
    url(r'^(?P<app_label>[^/]+)/(?P<module_name>[^/]+)/range/$', range_resource),
    url(r'^(?P<app_label>[^/]+)/(?P<module_name>[^/]+)/bulk/$', bulk_resource),
    url(r'^(?P<app_label>[^/]+)/(?P<module_name>[^/]+)/$', object_resource),
)