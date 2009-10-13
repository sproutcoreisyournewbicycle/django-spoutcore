import re
import decimal

from django.utils.encoding import force_unicode

def deconstruct(item):
    """
    Recursively loops through the item's children, converting them all
    to python types, falling back to calling Django's `force_unicode`.

    """
    if isinstance(item, dict):
        return dict([(k, deconstruct(v)) for k, v in item.iteritems()])
    elif isinstance(item, decimal.Decimal):
        return str(item)
    elif hasattr(item, '__iter__'):
        return [deconstruct(v) for v in item]
    elif callable(item):
        return None
    else:
        return force_unicode(item, strings_only=True)
 
def camelize(string):
    """
    Returns given string as CamelCased.
    
    Converts a string like "send_email" to "SendEmail". It will remove
    non-alphanumeric character from the string, so "who's online" will
    be converted to "WhoSOnline"
    
    """
    if string:
        string = force_unicode(string)
        string = ''.join(w[0].upper() + w[1:] for w in re.sub('[^A-Z^a-z^0-9^:]+', ' ', string).split(' ') if w)
    return string

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
    string = force_unicode(string)
    return  re.sub('[^A-Z^a-z^0-9^\/]+','_', \
            re.sub('([a-z\d])([A-Z])','\\1_\\2', \
            re.sub('([A-Z]+)([A-Z][a-z])','\\1_\\2', re.sub('::', '/',string)))).lower()

def splitwords(string):
    """Split camelized or underscored names into distinct words."""
    cam = list(string.replace('_',' '))
    uncam = [cam.pop(0)]
    while cam:
        c, u = cam.pop(0), uncam[-1]
        if c.isupper() and u.islower():
            uncam.append(' ')
        uncam.append(c)
    return ''.join(uncam).strip()
    








