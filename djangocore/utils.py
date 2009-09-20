import re
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.conf import settings
from django.utils.functional import Promise
from django.utils.encoding import smart_str


try:
    from piston.emitters import Emitter
    from piston.handler import typemapper

    class EmitterHttpResponse(HttpResponse):
        """
        An HttpResponse object that emits its content acording to the
        given format. Defaults to emitting `json`. Useful for when you
        want to return a response with encoded contents, that doesn't
        have a HTTP 200 status code.
        
        """
        def __init__(self, request, handler, content='', mimetype=None, \
          status=None, content_type=None, format='json'):
    
            emitter, mimetype = Emitter.get(format)
            if content:
                srl = emitter(content, typemapper, handler, handler.fields, \
                  handler.is_anonymous)
                content = srl.render(request)                
    
            super(EmitterHttpResponse, self).__init__(content, mimetype, \
              status, content_type)

except ImportError:
    pass
    

class SproutCoreJSONEncoder(DjangoJSONEncoder):
    """
    JSONEncoder subclass that knows how to deal with Django translation
    objects.
    """
    def default(self, o):
        if isinstance(o, Promise):
            return smart_str(o)

        try:
            return super(SproutCoreJSONEncoder, self).default(o)

        # If we get something that can't be encoded, then we just encode None.
        except TypeError:
            return None

def camelize(string):
    """
    Returns given string as CamelCased.
    
    Converts a string like "send_email" to "SendEmail". It will remove
    non-alphanumeric character from the string, so "who's online" will
    be converted to "WhoSOnline"
    
    """
    string = smart_str(string)
    return ''.join(w[0].upper() + w[1:] for w in re.sub('[^A-Z^a-z^0-9^:]+', ' ', string).split(' ') if w)

def lcamelize(string):
    """
    Returns given string as CamelCased, but with the first letter as
    lowercase.
    
    Converts a string like "send_email" to "sendEmail". It will remove
    non-alphanumeric character from the string, so "who's online" will
    be converted to "whoSOnline"
    
    """
    string = camelize(string)
    if string:
        string = string[0].lower() + string[1:]
    return string

def underscore(string):
    """
    Converts a string "into_it_s_underscored_version".
    
    Convert any "CamelCased" or "ordinary string" into an
    "underscored_string". This can be really useful for creating
    friendly URLs.
    
    """
    string = smart_str(string)
    return  re.sub('[^A-Z^a-z^0-9^\/]+','_', \
            re.sub('([a-z\d])([A-Z])','\\1_\\2', \
            re.sub('([A-Z]+)([A-Z][a-z])','\\1_\\2', re.sub('::', '/',string)))).lower()

