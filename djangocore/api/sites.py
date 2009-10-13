# Django dependencies.
from django.conf.urls.defaults import patterns, url, include

# Intra-app dependencies.
from djangocore.api.auth.authenticators import AnonymousAuthenticator

class AlreadyRegistered(Exception):
    pass

class NotRegistered(Exception):
    pass

class ResourceSite(object):
    def __init__(self, name=None, app_name='api'):
        self._registry = {}
        self._authenticator = AnonymousAuthenticator

        if name is None:
            name = 'api'
        self.name = name
        self.app_name = app_name
        
    def _get_authenticator(self):
        return self._authenticator
    authenticator = property(_get_authenticator)
    
    def set_authenticator(self, auth_class, *gateways, **options):
        """
        Set the ResourceSite to use the given Authenticator and Gateways
        as the default for all registered Resources.
        
        """
        # Dynamically construct a subclass of the given Authenticator with the
        # specified Gateways and options.
        if gateways:
            options['gateways'] = gateways
        options['__module__'] = __name__
        Authenticator = type(auth_class.__name__, (auth_class,), options)
        self._authenticator = Authenticator

    def register(self, resource_class, **options):
        # Dynamically construct a subclass of the given Resource with the specified
        # options.
        options['__module__'] = __name__
        Resource = type(resource_class.__name__, (resource_class,), options)

        resource = Resource(self)
        key = resource.url_prefix
        
        if key in self._registry:
            raise AlreadyRegistered("The resource %s is already registered at "
                "'%s'" % (Resource.__name__, key))
        self._registry[key] = resource
    
    def unregister(self, key, **options):
        if not isinstance(key, basestring):
            resource_class = key
            options['__module__'] = __name__
            Resource = type(resource_class.__name__, (resource_class,), options)
            
            resource = Resource(self)
            key = resource.url_prefix
        
        if not key in self._registry:
            raise NotRegistered('The resource %s is not registered' %
                Resource.__name__)
        del self._registry[key]

    def get_urls(self):
        urlpatterns = patterns('')
        for url_prefix, resource_class in self._registry.iteritems():
            # Add a carrot to the url_prefix if it doesn't already have one.
            if not url_prefix.startswith('^'):
                url_prefix = '^%s' % url_prefix
            
            urlpatterns += patterns('',
                url(url_prefix, include(resource_class.urls))
            )
        return urlpatterns
        
    def urls(self):
        return self.get_urls(), self.app_name, self.name
    urls = property(urls)

site = ResourceSite()

