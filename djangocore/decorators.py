from django.db.models import get_model
from django.http import HttpResponseForbidden, HttpResponseBadRequest, \
  HttpResponseNotAllowed
from django.conf import settings

def staff_member_required(func):
    """
    Makes sure the user requesting the page is a staff member.
    
    Unlike the Django's built-in `staff_member_required decorator`, this
    one does not display a login form, or redirect the user to a login
    form, if they are not a logged in staff member. It simply returns
    an HTTP 403 Forbidden response.
    
    @staff_member_required
    def my_view(request, model):
        ...
        
    """
    def wrap(request, *args, **kwargs):
        # User must be logged in, active, and staff.
        if not request.user.is_authenticated or \
          not request.user.is_staff:
            return HttpResponseForbidden
        
        return func(request, *args, **kwargs)
    
    wrap.__doc__ = func.__doc__
    wrap.__name__ = func.__name__
    return wrap

def permission_required(perm, *permissions):
    """
    Accepts a list of permissions, which each accept dictionary style
    formatting the keyword arguments passed to the wrapped function, and
    makes sure the requesting user has those permissions.
    
    Unlike Django's built-in `permission_required` decorator, this one
    accepts multiple required permissions and allows for dynamic
    permission checking at runtime, based on keyword values.
    
    @permission_required('%(app_label)s.change_%(module_name)s')
    def my_view(request, model):
        ...

    @permission_required('can_vote', 'can_drink', 'can_drive')
    def my_view(request, model):
        ...
    
    """
    # We use multiple permission arguments, so that the decorator will throw an
    # error if it's not passed at least one. We Merge them back together here.
    permissions = list(permissions) # convert from tuple
    permissions.append(perm)
    
    def decorator(func):
        def wrap(request, *args, **kwargs):
            # Format the passed permissions with any kwargs and make sure
            # that the user does have all indiciated permissions.
            required_permissions = [p % kwargs for p in permissions]
            if not request.user.has_perms(required_permissions):
                return HttpResponseForbidden
            
            return func(request, *args, **kwargs)
        
        wrap.__doc__ = func.__doc__
        wrap.__name__ = func.__name__
        wrap.__dict__.update(func.__dict__)
        return wrap
    
    return decorator

def get_model_from_kwargs(func=None, app_label_kwarg='app_label', \
  module_name_kwarg='module_name'):
    """
    Takes two keyword arguments::
        
        app_label_kwarg: the name of a keyword argument that maps to a
        model's app label. Defaults to `app_label`.
        
        module_name_kwarg: the name of a keyword argument that maps to a
        model's module_name. Defaults to `module_name`.
        
    When the decorated function is called, `get_model_from_kwargs` looks
    for the two specified keywords, and uses them to lookup an installed
    model. The model is then passed to the decorated function as the 
    second positional argument (after the request object), in place of
    the given keyword arguments.
    
    If the specified model doesn't exist, a HTTP 400 Bad Request is
    returned.
    
    @get_model_from_kwargs
    def my_view(request, model):
        ...

    @get_model_from_kwargs(app_label_kwarg='a', module_name_kwarg='m')
    def my_view(request, model):
        ...
    
    """        
    def decorator(func):
        def wrap(request, *args, **kwargs):
            app_label = kwargs.pop(app_label_kwarg)        
            module_name = kwargs.pop(module_name_kwarg)
    
            model = get_model(app_label, module_name)
            if not model:
                return HttpResponseBadRequest
    
            return func(request, model, *args, **kwargs)
        
        wrap.__doc__ = func.__doc__
        wrap.__name__ = func.__name__
        wrap.__dict__.update(func.__dict__)
        return wrap

    if func is None:
        # @get_model_from_kwargs() or
        # @get_model_from_kwargs(app_label_kwarg='app', module_name_kwarg='mod')
        return decorator
    else:
        # @get_model_from_kwargs or
        # @get_model_from_kwargs(func)
        return decorator(func)

def get_emitter_format(func, emitter_format=''):
    """
    Takes one keyword arguments::
        
        emitter_format: the emitter format for this handler. If not
        given, tries to look for a `format` GET parameter, and failing
        that, defaults to `json`.
        
    Unfortunately piston doesn't pass through the emitter_format keyword
    argument, which means this decorator can only detect the format if
    it is specified as a GET parameter.
    
    If you're explicitly specifying a particular output format (by
    passing a dictionary with an `emitter_format` key in it to the
    handler) this decorator can still help. Simply call the decorator,
    with the `format` keyword argument set to the same string used in
    the passed dictionary.

    If the emitter format is dynamically specified in the URL path
    itself, then there's no way for the decorator to retrieve it. The
    solution? Don't specify the emitter format as part of the URL path;
    only use GET parameters, or specify explicitly.
    
    @get_emitter_format
    def my_view(request, model):
        ...

    @get_emitter_format(format='json')
    def my_view(request, model):
        ...
    
    """        
    def decorator(func):
        def wrap(request, *args, **kwargs):
            kwargs['emitter_format'] = format or request.GET.get('format', 'json')
            return func(request, *args, **kwargs)
        wrap.__doc__ = func.__doc__
        wrap.__name__ = func.__name__
        return wrap

    if func is None:
        # @get_emitter_format() or
        # @get_emitter_format(format='json')
        return decorator
    else:
        # @get_emitter_format or
        # @get_emitter_format(func)
        return decorator(func)


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
    Simple decorator to require a GET request for a view.

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
    Simple decorator to require a POST request for a view.

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
    Simple decorator to require a PUT request for a view.

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
    Simple decorator to require a DELETE request for a view.

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
