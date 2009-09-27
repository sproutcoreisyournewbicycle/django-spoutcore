from django.conf.urls.defaults import *
from django.conf import settings
from django.utils import simplejson

from piston.resource import Resource
from piston.emitters import Emitter

from djangocore.utils import SproutCoreJSONEncoder
from djangocore.handlers import *

urlpatterns = patterns('',
    url(r'^(?P<app_label>[^/]+)/(?P<module_name>[^/]+)/length/$',   Resource(LengthHandler)),
    url(r'^(?P<app_label>[^/]+)/(?P<module_name>[^/]+)/range/$',    Resource(RangeHandler)),
    url(r'^(?P<app_label>[^/]+)/(?P<module_name>[^/]+)/bulk/$',     Resource(BulkHandler)),
    url(r'^(?P<app_label>[^/]+)/(?P<module_name>[^/]+)/$',          Resource(ObjectHandler)),
)

# Make it so piston can understand django's translation objects.
class SproutCoreJSONEmitter(Emitter):
    def render(self, request):
        cb = request.GET.get('callback')
        seria = simplejson.dumps(self.construct(), cls=SproutCoreJSONEncoder, ensure_ascii=False, indent=4)
        if cb:
            return '%s(%s)' % (cb, seria)
        return seria
Emitter.register('json', SproutCoreJSONEmitter, 'application/json; charset=utf-8')

# Have all emitters send responses in plain text when debugging. This makes it
# easy to view responses directly in your browser.
if settings.DEBUG:
    for key, (emitter, ct) in Emitter.EMITTERS.items():
        # Replace the content type for all emitters with 'text/plain'.
        Emitter.EMITTERS[key] = (emitter, 'text/plain; charset=utf-8')