import re

from django.http import HttpResponseBadRequest
from django.conf import settings

from django.http import HttpResponse
from django.utils import simplejson
from django.core.mail import mail_admins
from django.utils.translation import ugettext as _
import sys

# TO DO: Create working decorators for returning JSON and Serialized models.
#def json_view(func):
#    def wrap(request, *a, **kw):
#        response = None
#        try:
#            response = func(request, *a, **kw)
#            assert isinstance(response, dict)
#            if 'result' not in response:
#                response['result'] = 'ok'
#        except Exception, e:
#            # Come what may, we're returning JSON.
#            if hasattr(e, 'message'):
#                msg = e.message
#            else:
#                msg = _('Internal error')+': '+str(e)
#            response = {'result': 'error',
#                        'text': msg}
#
#        json = simplejson.dumps(response)
#        return HttpResponse(json, mimetype='application/json')
#    return wrap
#    
#def serialize_view(func):
#    def wrap(request, *a, **kw):
#        response = None
#        try:
#            qs = func(request, *a, **kw)
#            assert isinstance(response, dict)
#            if 'result' not in response:
#                response['result'] = 'ok'
#        except Exception, e:
#            # Come what may, we're returning JSON.
#            if hasattr(e, 'message'):
#                msg = e.message
#            else:
#                msg = _('Internal error')+': '+str(e)
#            response = {'result': 'error',
#                        'text': msg}
#
#        json = simplejson.dumps(response)
#        return HttpResponse(json, mimetype='application/json')
#    return wrap

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

# decorators
def POST_required(func):
    def decorated(request, *args, **kwargs):
        if request.method != 'POST':
            return HttpResponseNotAllowed('Only POST here')
        return func(request, *args, **kwargs)
    return decorated

def GET_required(func):
    def decorated(request, *args, **kwargs):
        if request.method != 'GET':
            return HttpResponseNotAllowed('Only GET here')
        return func(request, *args, **kwargs)
    return decorated

def PUT_required(func):
    def decorated(request, *args, **kwargs):
        if request.method != 'PUT':
            return HttpResponseNotAllowed('Only PUT here')
        return func(request, *args, **kwargs)
    return decorated

def DELETE_required(func):
    def decorated(request, *args, **kwargs):
        if request.method != 'DELETE':
            return HttpResponseNotAllowed('Only DELETE here')
        return func(request, *args, **kwargs)
    return decorated



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

