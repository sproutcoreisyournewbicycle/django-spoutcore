import re

from django.http import HttpResponseBadRequest
from django.conf import settings

def ajax_required(f):
    """
    AJAX request required decorator
    use it in your views:

    @ajax_required
    def my_view(request):
        ....

    """    
    def wrap(request, *args, **kwargs):
            if not request.is_ajax() and not settings.DEBUG:
                return HttpResponseBadRequest
            return f(request, *args, **kwargs)
    wrap.__doc__=f.__doc__
    wrap.__name__=f.__name__
    return wrap

def camelize(string):
    """
    Returns given string as CamelCased.
    
    Converts a string like "send_email" to "SendEmail". It will remove
    non-alphanumeric character from the string, so "who's online" will
    be converted to "WhoSOnline"
    
    """
    return ''.join(w[0].upper() + w[1:] for w in re.sub('[^A-Z^a-z^0-9^:]+', ' ', string).split(' ') if w)

def underscore(string):
    """
    Converts a string "into_it_s_underscored_version".
    
    Convert any "CamelCased" or "ordinary string" into an
    "underscored_string". This can be really useful for creating
    friendly URLs.
    
    """
    return  re.sub('[^A-Z^a-z^0-9^\/]+','_', \
            re.sub('([a-z\d])([A-Z])','\\1_\\2', \
            re.sub('([A-Z]+)([A-Z][a-z])','\\1_\\2', re.sub('::', '/',string)))).lower()

