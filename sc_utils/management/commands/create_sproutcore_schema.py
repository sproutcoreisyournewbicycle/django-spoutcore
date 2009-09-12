import os.path
from django.core.management.base import NoArgsCommand
from django.core.management.color import no_style
from django.utils.importlib import import_module
from optparse import make_option
import sys, os
from shutil import copy
from django.db import models
from django.template import loader, Context
from django.conf import settings
from utils.inflector.Inflector import Inflector
inflector = Inflector()
try:
    set
except NameError:
    from sets import Set as set   # Python 2.3 fallback

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
    )
    help = "Create the sprout core models for all apps in INSTALLED_APPS \
            whose models haven't already been created. For those already \
            created, subclass files will not be overwritten."

    def handle_noargs(self, **options):
        # from django.core.management.sql import custom_sql_for_model, emit_post_sync_signal

        verbosity = int(options.get('verbosity', 1))
        interactive = options.get('interactive')
        show_traceback = options.get('traceback', False)

        self.style = no_style()

        # Import the 'management' module within each installed app, to register
        # dispatcher events.
        for app_name in settings.INSTALLED_APPS:
            try:
                import_module('.management', app_name)
            except ImportError, exc:
                # This is slightly hackish. We want to ignore ImportErrors
                # if the "management" module itself is missing -- but we don't
                # want to ignore the exception if the management module exists
                # but raises an ImportError for some reason. The only way we
                # can do this is to check the text of the exception. Note that
                # we're a bit broad in how we check the text, because different
                # Python implementations may not use the same text.
                # CPython uses the text "No module named management"
                # PyPy uses "No module named myproject.myapp.management"
                msg = exc.args[0]
                if not msg.startswith('No module named') or 'management' not in msg:
                    raise
                print app_name

#        cursor = connection.cursor()

        # Get a list of already installed *models* so that references work right.
#        tables = connection.introspection.table_names()
#        seen_models = connection.introspection.installed_models(tables)
#TODO: check for files here
        created_models = set()
        pending_references = {}
        os.chdir(settings.PROJECT_ROOT)
        if not os.path.exists ("sproutcore/frameworks/"):
            os.makedirs ("sproutcore/frameworks/")
        # Create the tables for each model
        for app in models.get_apps():

            app_name = app.__name__.split('.')[-2]
            model_list = models.get_models(app)
            os.chdir(settings.PROJECT_ROOT + "/sproutcore/frameworks/")
            try:
                os.mkdir(app_name)
                os.chdir(app_name)
                os.mkdir('_generated')
            except OSError:
                os.chdir(app_name)
            for model in model_list:
                # Create the model's file, if it doesn't already exist.
    #            import pdb; pdb.set_trace()
                file_name = inflector.underscore(model.__name__) + ".js"
                generated_folder_path = settings.PROJECT_ROOT + "/sproutcore/frameworks/" + app_name + "/" "_generated/"
                generated_file_name = "_" + file_name
   #             import pdb; pdb.set_trace()
                if not os.path.exists(file_name):
                    f = open(file_name, 'wb')
                    t = loader.get_template('sc_utils/sproutcore_generated.html')
                    c = Context({'model': inflector.classify(model.__name__), 'app': inflector.classify(app_name)})
                    rendered = t.render(c)
                    f.write(rendered)
                    f.close()
                    
                    #open and write the generated file as well
                    os.chdir(generated_folder_path)
                    f = open(generated_file_name, 'wb')
                    t = loader.get_template('sc_utils/user.html')
                    c = Context({
                                'model': inflector.classify(model.__name__),
                                'app': inflector.classify(app_name),
                                'folder': model.__name__
                            })
                    rendered = t.render(c)
                    f.write(rendered)
                    f.close()
                    os.chdir('..')

                    
                    if verbosity >= 2:
                        print "Processing %s.%s model" % (app_name, model._meta.object_name)
    #                seen_models.add(model)#TODO: Change to file list
                    created_models.add(model)
                    if verbosity >= 1:
                        print "Creating file for %s" % model._meta.db_table


        # Create the m2m tables. This must be done after all tables have been created
        # to ensure that all referred tables will exist.
#        for app in models.get_apps():
#            app_name = app.__name__.split('.')[-2]
#            model_list = models.get_models(app)
#            for model in model_list:
#                if model in created_models:
#                    if True:
#                        if verbosity >= 2:
#                            print "Creating many-to-many tables for %s.%s model" % (app_name, model._meta.object_name)

        # Send the post_syncdb signal, so individual apps can do whatever they need
        # to do at this point.
#        emit_post_sync_signal(created_models, verbosity, interactive)


        # Install the 'initial_data' fixture, using format discovery
#        from django.core.management import call_command
#        call_command('loaddata', 'initial_data', verbosity=verbosity)

