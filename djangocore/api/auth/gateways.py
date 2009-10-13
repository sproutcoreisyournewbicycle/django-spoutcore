class BaseGateway(object):
    """
    Provides client identification logic (i.e. login) and optionally
    a set of urls to facilitate client identification (e.g. login or
    logout urls).    
    
    """
    
    def __init__(self, resource_site, authenticator, resource):
        self.resource_site = resource_site
        self.authenticator = authenticator
        self.resource = resource
    
    def get_user(self, request):
        raise NotImplementedError

class CookieDjangoUserGateway(BaseGateway):
    """
    A simple gateway which looks for clients that are logged in with
    Django's existing auth system.
    """
    def get_user(self, request):
        if request.user.is_authenticated():
            return request.user
        
        return None

class TokenDjangoUserGateway(BaseGateway):
    token_field_name = None
    
    def get_user(self, request):
        token = request.GET.get('token', None)
        if token:
            from django.contrib.auth.models import User
            from django.core.exceptions import MultipleObjectsReturned
            
            lookups = {}
            lookups[token_field_name] = token
            try:
                return User.objects.get(**lookups)
            except User.DoesNotExist, MultipleObjectsReturned:
                pass
        return None





