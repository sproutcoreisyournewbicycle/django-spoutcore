from django.conf.urls.defaults import *
from django.conf import settings

from piston.resource import Resource
from djangocore.handlers import *

urlpatterns = patterns('',
    url(r'^(?P<app_label>[^/]+)/(?P<module_name>[^/]+)/length/$',   Resource(LengthHandler)),
    url(r'^(?P<app_label>[^/]+)/(?P<module_name>[^/]+)/range/$',    Resource(RangeHandler)),
    url(r'^(?P<app_label>[^/]+)/(?P<module_name>[^/]+)/bulk/$',     Resource(BulkHandler)),
    url(r'^(?P<app_label>[^/]+)/(?P<module_name>[^/]+)/$',          Resource(ObjectHandler)),
)

# Have all emitters send responses in plain text when debugging. This makes it
# easy to view responses directly in your browser.
if settings.DEBUG:
    from piston.emitters import Emitter
    for key, (emitter, ct) in Emitter.EMITTERS.items():
        # Replace the content type for all emitters with 'text/plain'.
        Emitter.EMITTERS[key] = (emitter, 'text/plain; charset=utf-8')
            