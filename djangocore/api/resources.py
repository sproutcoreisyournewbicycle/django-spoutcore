# Django dependencies.
from django.http import HttpResponseNotAllowed, Http404
from django.conf.urls.defaults import patterns, url, include

# Intra-app dependencies.
from djangocore.utils import underscore
from djangocore.serialization import mimer, MalformedData, EmittableResponse


class BaseResource(object):
    """
    Encapsulates all of the basic resuable building blocks necessary for
    creating a Resource class.
    
    """
    anonymous = False # When set to True, skips authenticating requests entirely.
    allowed_operations = () # Filters handler functions if given. See `ops` below.
    
    class Auth:
        pass
    
    @classmethod
    def set_authenticator(cls, auth_class, *gateways):
        """
        Set the ResourceSite to use the given Authenticator and Gateways
        as the default for all registered Resources.
        
        """
        # Dynamically construct a subclass of the given Authenticator with the
        # specified Gateways and options.
        options = {}
        if gateways:
            options['gateways'] = gateways
        options['__module__'] = __name__
        Authenticator = type(auth_class.__name__, (auth_class,), options)
        self._authenticator = Authenticator
    
    def __init__(self, resource_site):
        self.resource_site = resource_site

        # Create a new Authenticator with all of the options specified in the
        # resource's inner Auth class.
        auth = getattr(self, '_authenticator', resource_site.authenticator)
        self.authenticator = auth(self.resource_site, self, self.Auth)

    def ops(self, **ops):
        """
        Helper function which takes keyword arguments mapping HTTP
        methods to handler function names, and returns a dictionary
        of allowed methods and the actual handler functions.
        
        """
        return dict([(m.upper(), getattr(self, op)) for m, op in ops.items()
          if op in self.allowed_operations or not self.allowed_operations])

    def get_urls(self):
        """
        Returns a urlpatterns object mapping urls and request methods
        for this resource to the appropriate data handler functions.
        
        """
        raise NotImplementedError

    def urls(self):
        return self.get_urls()
    urls = property(urls)

    def get_url_prefix(self):
        """
        Returns the prefix where this Resource's urls will be hooked up.
        
        """
        return 'resource/%s/' % underscore(self.__class__.__name__)
    
    def url_prefix(self):
        return self.get_url_prefix()
    url_prefix = property(url_prefix)

    def is_authenticated(self, request, handler):
        """
        Returns True if the request should be carried out; false if not.
        
        """
        # For anonymous resources we skip authentication entirely.
        if self.anonymous:
            return True
        return self.authenticator.is_authenticated(request, handler)
    
    def process_request(self, request):
        """
        Preprocess the request before sending it off to the handler
        functions.
        
        """
        # Deserialize the data we recieved, if any.
        if request.method in ('PUT', 'POST'):
            mimer.translate(request)
    
    def mapper(self, request, **ops):
        """
        Maps a given url and request method to a given handler function.
        
        """
        if not ops:
            # There are no allowed operations for the given URL.
            raise Http404
        
        handler = ops.get(request.method, None)
        
        if not handler:
            # The request method isn't allowed for the given URL.
            return HttpResponseNotAllowed(ops.keys())
        
        if not self.is_authenticated(request, handler):
            return EmittableResponse("", status=403)
                
        try:
            self.process_request(request)
        except MalformedData, err:
            # The data sent in the request was malformed.
            return EmittableResponse(str(err), status=400)
        
        response = handler(request)

        response = self.process_response(response, request)
        return response

# TODO: Add in some way to catch errors...        
#
#        from djangocore.api.utils import Bubbler
#        try:
#           ...
#        except Bubbler:
#            return Bubbler.contents
