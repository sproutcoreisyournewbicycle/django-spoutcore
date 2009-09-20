import re
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.functional import Promise
from django.utils.encoding import smart_str

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

