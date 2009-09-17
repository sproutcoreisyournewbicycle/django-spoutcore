import re
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed
from django.conf import settings

def ajax_required(func):
    """
    Simple decorator to require an AJAX request for a view.

    @ajax_required
    def my_view(request):
        ...

    """    
    def wrap(request, *args, **kwargs):
        if not request.is_ajax() and not settings.DEBUG:
            return HttpResponseBadRequest
        return func(request, *args, **kwargs)
    wrap.__doc__ = func.__doc__
    wrap.__name__ = func.__name__
    return wrap

def get_required(func):
    """
    Simple decorator to require an GET request for a view.

    @get_required
    def my_view(request):
        ...

    """    
    def wrap(request, *args, **kwargs):
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])
        return func(request, *args, **kwargs)
    wrap.__doc__ = func.__doc__
    wrap.__name__ = func.__name__
    return wrap

def post_required(func):
    """
    Simple decorator to require an POST request for a view.

    @post_required
    def my_view(request):
        ...

    """    
    def wrap(request, *args, **kwargs):
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST'])
        return func(request, *args, **kwargs)
    wrap.__doc__ = func.__doc__
    wrap.__name__ = func.__name__
    return wrap

def put_required(func):
    """
    Simple decorator to require an PUT request for a view.

    @put_required
    def my_view(request):
        ...

    """    
    def wrap(request, *args, **kwargs):
        if request.method != 'PUT':
            return HttpResponseNotAllowed(['PUT'])
        return func(request, *args, **kwargs)
    wrap.__doc__ = func.__doc__
    wrap.__name__ = func.__name__
    return wrap

def delete_required(func):
    """
    Simple decorator to require an DELETE request for a view.

    @delete_required
    def my_view(request):
        ...

    """    
    def wrap(request, *args, **kwargs):
        if request.method != 'DELETE':
            return HttpResponseNotAllowed(['DELETE'])
        return func(request, *args, **kwargs)
    wrap.__doc__ = func.__doc__
    wrap.__name__ = func.__name__
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

