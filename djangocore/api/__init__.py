"""
Copied from Django's admin app.

"""
import os

from django.utils.importlib import import_module

from djangocore.api.sites import site

# A flag to tell us if autodiscover is running.  autodiscover will set this to
# True while running, and False when it finishes.
LOADING_API = False

def autodiscover():
    """
    Auto-discover INSTALLED_APPS api.py modules and fail silently when
    not present. This forces an import on them to register any api bits they
    may want.
    """
    # Bail out if autodiscover didn't finish LOADING_API from a previous call so
    # that we avoid running autodiscover again when the URLconf is loaded by
    # the exception handler to resolve the handler500 view.  This prevents an
    # api.py module with errors from re-registering models and raising a
    # spurious AlreadyRegistered exception (see #8245).
    global LOADING_API
    if LOADING_API:
        return
    LOADING_API = True

    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        # For each app, we need to look for an api.py inside that app's
        # package. We can't use os.path here -- recall that modules may be
        # imported different ways (think zip files) -- so we need to get
        # the app's __path__ and look for api.py on that path.

        # Step 1: find out the app's __path__ Import errors here will (and
        # should) bubble up, but a missing __path__ (which is legal, but weird)
        # fails silently -- apps that do weird things with __path__ might
        # need to roll their own api registration.
        try:
            app_path = import_module(app).__path__
        except AttributeError:
            continue

        # Step 2: import the app's api file. If this has errors we want them
        # to bubble up. import_module raises ImportError if the module can't be
        # found, so we catch those and skip the app.
        if os.path.exists(app_path[0] + '/api.py'):
            import_module("%s.api" % app)

    # autodiscover was successful, reset LOADING_API flag.
    LOADING_API = False
