try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

try:
    import yaml
except ImportError:
    yaml = None


from django.conf import settings
from django.utils import simplejson
from django.utils.encoding import force_unicode
from django.utils.xmlutils import SimplerXMLGenerator
from django.http import HttpResponse, HttpResponseBadRequest
from django.core.serializers.json import DjangoJSONEncoder 

from djangocore.utils import deconstruct

class EmittableResponse(object):
    """A thin wrapper for returning an HttpResponse whose contents can be 
    serialized."""
    def __init__(self, content, **ops):
        self.content = content
        self.ops = ops

class AlreadyRegistered(Exception):
    """Raised when trying to register a content type that has already
    been registered."""
    pass

class NotRegistered(Exception):
    """Raised when trying to unregister a content type that isn't
    registered."""
    pass

class MalformedData(Exception):
    """Raised when loading the data in the request body fails."""
    pass
    
class Mimer(object):
    def __init__(self):
        self._registry = {}
        
    def register(self, ctype_or_iterable, mimer):
        if isinstance(ctype_or_iterable, basestring):
            ctype_or_iterable = [ctype_or_iterable]
        for ctype in ctype_or_iterable:
            if ctype in self._registry:
                raise AlreadyRegistered("The content type %s is already "
                  "registered" % ctype)
            self._registry[ctype] = mimer
        
    def unregsiter(self, ctype_or_iterable):
        if isinstance(ctype_or_iterable, basestring):
            ctype_or_iterable = [ctype_or_iterable]
        for ctype in ctype_or_iterable:
            if ctype not in self._registry:
                raise NotRegistered("The content type %s is not registered"
                  % ctype)
            del self._registry[ctype]
    
    def mimer_for_ctype(self, ctype):
        return self._registry.get(ctype, None)

    def content_type(self, request):
        """
        Returns the content type of the request, except when the request
        is form-encoded or contains multipart form data.
        
        """
        formencoded_ctype = "application/x-www-form-urlencoded"

        ctype = request.META.get('CONTENT_TYPE', formencoded_ctype).strip()
        if ctype.startswith(formencoded_ctype) or ctype.startswith('multipart'):
            return None
        
        return ctype

    def translate(self, request):
        """
        Looks at the ``Content-type`` header sent by the client, and
        attempts to deserialize the contents into the specified format.
        
        This works for JSON and YAML. The deserialized data is placed in
        ``request.data`` since it is not necessarily a simple list of
        key-value pairs.
        
        Also sets ``request.content_type``. ``request.content_type``
        will be set to None for form-encoded or multipart form data.
        
        """    
        ctype = self.content_type(request)
        request.content_type = ctype
        request.data = None
        
        # For PUT requests we have to force django to load the request data.
        if request.method == "PUT":
            try:
                request.method = "POST"
                request._load_post_and_files()
                request.method = "PUT"
            except AttributeError:
                request.META['REQUEST_METHOD'] = "POST"
                request._load_post_and_files()
                request.META['REQUEST_METHOD'] = "PUT"
                
        if ctype:
            mimer = self.mimer_for_ctype(ctype)
            if mimer:
                try:
                    request.data = mimer(request.raw_post_data)
                        
                except (TypeError, ValueError):
                    raise MalformedData("The '%s' data sent in the request was "
                      "malformed" % ctype)
        
        elif request.method in ("PUT", "POST"):
            # The data for PUT requests still resides in the POST variable,
            # since we tricked django into loading it as POST data.
            request.data = request.POST
            
        # To reduce confusion, reset POST and PUT, since the data now resides
        # in the request.data variable.
        request.POST = {}
        
        return request

class Emitter(object):
    def __init__(self):
        self._registry = {}

    def register(self, format, emitter, ctype):
        if format in self._registry:
            raise AlreadyRegistered("The emitter for %s is already registered"
              % format)
        self._registry[format] = (emitter, ctype)
        
    def unregsiter(self, format):
        if name not in self._registry:
            raise NotRegistered("The emitter for %s is not registered" % format)
        del self._registry[format]
    
    def emitter_for_format(self, format):
        return self._registry.get(format, (None, None))
                    
    def translate(self, format, response):
        # We catch and return any HttpResponses here for convenience's sake.
        # This really should be the developers responsibility
        if isinstance(response, HttpResponse):
            return response

        emitter, ctype = self.emitter_for_format(format)
        
        if emitter and ctype:
            # Set the content type to text/plain when in debug mode, so that the
            # response will be viewable within the browser.
            if settings.DEBUG:
                ctype = 'text/plain; charset=utf-8'

            ops = {'content_type': ctype}            
            if isinstance(response, EmittableResponse):
                ops.update(response.ops)
                response = response.content
            
            # Deconstruct the response, serializer it, and then create a new
            # HttpResponse with the given options specified.
            response = deconstruct(response)
            return HttpResponse(emitter(response), **ops)
        
        return HttpResponseBadRequest("Cannot to serialize response to '%s' "
            "format specified in request" % format)        
    
mimer = Mimer()
emitter = Emitter()

mimer.register('application/json', lambda s: simplejson.loads(s))
emitter.register('json', lambda s: simplejson.dumps(s,
    cls=DjangoJSONEncoder, ensure_ascii=False, indent=4),
    'application/json; charset=utf-8')

if yaml:
    # YAML doesn't have an official mimetype, so we go with the common ones.
    mimer.register(('text/yaml', 'text/x-yaml', 'application/yaml', 
        'application/x-yaml'), lambda s: dict(yaml.load(s)))
    emitter.register('yaml', lambda s: yaml.safe_dump(s),
        'text/x-yaml; charset=utf-8')

def dump_xml(data):
    """Simple function to convert python data structures to xml."""
    def _to_xml(xml, data):
        if isinstance(data, dict):
            for key, value in data.iteritems():
                key = force_unicode(key)
                xml.startElement(key, {})
                _to_xml(xml, value)
                xml.endElement(key)
        elif hasattr(data, '__iter__'):
            for item in data:
                xml.startElement("resource", {})
                _to_xml(xml, item)
                xml.endElement("resource")
        else:
            xml.characters(force_unicode(data))

    stream = StringIO.StringIO()
    
    xml = SimplerXMLGenerator(stream, "utf-8")
    xml.startDocument()
    xml.startElement("response", {})
    
    _to_xml(xml, data)
    
    xml.endElement("response")
    xml.endDocument()
    
    return stream.getvalue()

emitter.register('xml', lambda s: dump_xml(s), 'text/xml; charset=utf-8')