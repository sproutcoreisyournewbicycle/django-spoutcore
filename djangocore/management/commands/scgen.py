# Standard library dependencies.
from optparse import make_option
import os

# Django dependencies.
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_app, get_apps, get_models, get_model, Model
from django.template.loader import render_to_string
from django.conf import settings

# Intra-app dependencies.
from djangocore.utils import camelize, underscore
from djangocore.transform import *

try:
    from appengine_django.models import BaseModel
except:
    BaseModel = None

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-d', '--directory', default='sproutcore/', dest='directory',
            help='Specifies the output directory for the files.'),
        make_option('-p', '--app-prefix', default='', dest='app_prefix',
            help='Specifies a prefix to prepend to all SproutCore app names.'),
        make_option('-e', '--exclude', dest='exclude', action='append', 
            default=[], help='App to exclude (use multiple --exclude to exclude multiple apps).'),
    )
    help = 'Generates valid SproutCore model schemas for all apps in \
            INSTALLED_APPS. Subclassed models will not be overwritten.'
    args = '[appname ...]'

    def handle(self, *app_labels, **options):
        project_name = os.environ['DJANGO_SETTINGS_MODULE'].split('.')[-2]
        directory = options.get('directory', None)
        app_prefix = options.get('app_prefix', \
          getattr(settings, 'SPROUTCORE_APP_PREFIX', ''))
        
        # This part of the code used to be one line, until we decided to check
        # that SPROUTCORE_ROOT starts with a '/'. Now we have to do hula hoops!
        if not directory:
            directory = getattr(settings, 'SPROUTCORE_ROOT', '')
            if directory and directory.startswith('/'):
                raise ValueError, "SPROUTCORE_ROOT must be an absolute path " \
                  "(and start with a '/')"
        
        # Make sure the specified directory ends with a '/' since it's a folder.
        if directory and not directory.endswith('/'):
            directory += '/'

        # Create the full directory structure.
        directory += 'frameworks/' + project_name
        
        exclude = options.get('exclude', [])
        
        try:
            # Exclude the AppEnginer helper, if it's installed, since we don't
            # want to include the BaseModel class in our transformations.
            excluded_apps = [get_app('appengine_django')]
        except ImproperlyConfigured:
            excluded_apps = []
        
        excluded_apps += [get_app(app_label) for app_label in exclude]

        if len(app_labels) == 0:
            app_list = dict([(app, None) for app in get_apps() if app not in excluded_apps])
        else:
            app_list = {}
            for label in app_labels:
                try:
                    app_label, model_label = label.split('.')
                    try:
                        app = get_app(app_label)
                    except ImproperlyConfigured:
                        raise CommandError("Unknown application: %s" % app_label)

                    model = get_model(app_label, model_label)
                    if model is None:
                        raise CommandError("Unknown model: %s.%s" % (app_label, model_label))

                    if app in app_list.keys():
                        if app_list[app] and model not in app_list[app]:
                            app_list[app].append(model)
                    else:
                        app_list[app] = [model]
                except ValueError:
                    # This is just an app - no model qualifier
                    app_label = label
                    try:
                        app = get_app(app_label)
                    except ImproperlyConfigured:
                        raise CommandError("Unknown application: %s" % app_label)
                    app_list[app] = None

        # Create the main SproutCore directory.
        if not os.path.exists(directory):
            os.makedirs(directory)
        os.chdir(directory)

        cwd = os.getcwd()
        
        app_labels = []    
        for app, model_list in app_list.items():
            if model_list is None:
                model_list = get_models(app)

            # Only create a directory for the app if it has models.
            if model_list:
                app_label = app.__name__.split('.')[-2]
                app_labels.append(app_label)
                
                # Create the directory structure for the app.
                path = 'frameworks/%s/_generated/' % app_label
                if not os.path.exists(path):
                    os.makedirs(path)
                os.chdir('frameworks/' + app_label)
                
                app_label = app_prefix + camelize(app_label)
                # Create the core.js file.
                f = open('core.js', 'w')
                rendered = render_to_string('djangocore/core.js', {
                    'app_label': app_label,
                })
                
                f.write(rendered)
                f.close()

                # Create the generated and user files for each model.
                for model in model_list:
                    file_name = underscore(model._meta.module_name) + ".js"
                    generated_file_name = '_generated/' + file_name
                    
                    # Make sure BaseModel was imported before we test with it.
                    if BaseModel and issubclass(model, BaseModel):
                        # AppEngine doesn't support meta options such as
                        # verbose_name, so we have to fall back to module_name.
                        model_name = camelize(model._meta.module_name)
                        data = appengine_transformer.get_model_data(model)

                    elif issubclass(model, Model):
                        # Just a regular Django model. Nothing special here.
                        model_name = camelize(model._meta.verbose_name)                        
                        data = django_transformer.get_model_data(model)
    
                    # Write the generated file to disk.
                    f = open(generated_file_name, 'w')
                    data.update({
                        'app_label': app_label,
                        'model_name': model_name,
                    })
                    rendered = render_to_string('djangocore/generated.js', data)
                    
                    f.write(rendered)
                    f.close()

                    # If the user file already exists, then we don't change it.
                    if not os.path.exists(file_name):
                        f = open(file_name, 'w')
                        rendered = render_to_string('djangocore/user.js', {
                            'generated_file_name' : generated_file_name,
                            'app_label': app_label,
                            'model_name': model_name,
                        })
                        
                        f.write(rendered)
                        f.close()
                    
                # Move back out to the main directory. 
                os.chdir('../..')

        f = open('BuildFile', 'w')
        rendered = render_to_string('djangocore/Buildfile', {
            'wrapper_framework': project_name,
            'frameworks': ',\n'.join([r"'" + a + r"'" for a in app_labels]),
        })
        
        f.write(rendered)
        f.close()
