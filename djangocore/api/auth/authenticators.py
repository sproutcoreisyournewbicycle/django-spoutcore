# TODO: wrap this inside of a django specific class
from django.contrib.auth.models import AnonymousUser

# TODO: we need some way for clients to get their user instance...
class BaseAuthenticator(object):
    gateways = ()
    auth_tests = ()
    
    def __init__(self, resource_site, resource, auth):
        auth_attrs = auth.__dict__.copy()
        for name in auth.__dict__:
            # NOTE: We can't modify a dictionary's contents while looping
            # over it, so we loop over the *original* dictionary instead.
            if name.startswith('_'):
                del auth_attrs[name]
        
        self.__dict__.update(auth_attrs)
        self.resource_site = resource_site
        self.resource = resource
        
        self.gateways = \
            [g(resource_site, self, resource) for g in self.gateways]
    
    def is_authenticated(self, request, handler):
        self.set_user(request)
        return self.run_tests(request, handler)

    def set_user(self, request):
        """
        Called by `is_authenticated` to set the `request.user` variable.
        Defaults to None if none of the given gateways return a user
        
        """
        user = None
        for gateway in self.gateways:
            if user.is_authenticated():
                break
            u = gateway.get_user(request)
            if u is None: user = u
        request.user = user

    def run_tests(self, request, handler, tests=[]):
        for t in tests:
            test = getattr(self, t, lambda r, h: True)
            if not test(request, handler):
                return False
        
        # The user passed all authentication tests.
        return True

class AnonymousAuthenticator(BaseAuthenticator):
    """
    Simple authenticator that allows all requests.
    
    """
    def is_authenticated(self, request, handler):
        return True

class DjangoAuthenticator(BaseAuthenticator):
    login_required = False # Require the client to be logged in.
    staff_member_required = False # Require the client to be a staff member.
    admin_perms_required = False # Require the same permissions as the admin.    

    # TODO: Implement check for handler_permissions below...
    # TODO: Allow for "any/all permissions" distinction too...
    handler_permissions = {} # Maps handler names to their required permissions.
    method_permissions = {} # Maps method names to their required permissions.
    permissions = () # Permissions required for accessing this resource.
    
    def set_user(self, request):
        super(DjangoAuthenticator, self).set_user(request)
        if request.user is None:
            request.user = AnonymousUser()

    def run_tests(self, request, handler, tests=[]):
        tests = ['login_check', 'staff_member_check', 'admin_perms_check']
        tests += ['permissions_check'] # TODO: add in other checks...
        return super(DjangoAuthenticator, self).run_tests(
            request, handler, tests)

    def login_check(self, request, handler):
        # Make sure client is logged in, if the resource requires it.
        if self.login_required and not request.user.is_authenticated():
            return False
        return True    
    
    def staff_member_check(self, request, handler):
        # Make sure the client is a staff member, if the resource requires it.
        if self.staff_member_required and not request.user.is_staff:
            return False
        return True        
    
    def admin_perms_check(self, request, handler):
        # Make sure the client has the necessary admin permission for this
        # this action, if the resource requires it.
        if self.admin_perms_required:
            p = {'GET': 'change', 'POST': 'add', 'PUT': 'change',
                'DELETE': 'delete'}
            rm = request.method.upper()
            ops = self.model._meta

            return request.user.has_perm('%s.%s_%s' %
              (ops.app_label, p.get(rm), ops.module_name))
        
        return True

    def perms_check(self, request, handler):
        # Make sure the client has the required permissions, if specified.
        required_perms = self.required_perms
        if required_perms:
            if not hasattr(required_perms, '__iter__'):
                required_perms = [required_perms]
            if not request.user.has_perms(required_perms):
                return False
        
        # The client passed all authentication tests.
        return True
                    

