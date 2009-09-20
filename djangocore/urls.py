from django.conf.urls.defaults import *
from django.conf import settings

from djangocore.handlers import length_resource, range_resource, bulk_resource, object_resource

urlpatterns = patterns('',
    url(r'^(?P<app_label>[^/]+)/(?P<module_name>[^/]+)/length/$', length_resource),
    url(r'^(?P<app_label>[^/]+)/(?P<module_name>[^/]+)/range/$', range_resource),
    url(r'^(?P<app_label>[^/]+)/(?P<module_name>[^/]+)/bulk/$', bulk_resource),
    url(r'^(?P<app_label>[^/]+)/(?P<module_name>[^/]+)/$', object_resource),
)

# Have all emitters send responses in plain text when debugging. This makes it
# easy to view responses directly in your browser.
if settings.DEBUG:
    from piston.emitters import Emitter
    for key, (emitter, ct) in Emitter.EMITTERS.items():
        # Replace the content type for all emitters with 'text/plain'.
        Emitter.EMITTERS[key] = (emitter, 'text/plain; charset=utf-8')
            