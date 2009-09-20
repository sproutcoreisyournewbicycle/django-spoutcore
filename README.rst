Overview
========
The django-sproutcore library is made up of several parts.

#. An ``scgen`` management command, which generates best-guess matching SproutCore models from you Django models.
#. A SproutCore admin interface for your server-side Django models that can replace (eventually) Django's own built-in admin app. The admin interface makes use of ``scgen``'s model generation.
#. Helpers for providing a RESTful API for custom SproutCore applications.

Requirements
============
The ``scgen`` command has no external dependencies (aside from Django, obviously).

To use the SproutCore admin interface, or the REST API helpers, it is necessary to install the wonderful `django-piston <http://bitbucket.org/jespern/django-piston/>`_ framework, as it is used for providing the basic REST interface.

Using ``scgen`` to generate SproutCore models
=============================================
django-sproutcore comes with an ``scgen`` Django management command which allows you to auto-generate best guess SproutCore models from your django models. This can help greatly speed up initial SproutCore development and prototyping.

The command can be run like any other Django management command. After adding the djangocore app to ``INSTALLED_APPS`` in your project's ``settings.py`` file, ``cd`` to your project directory and run ``python manage.py scgen``. If successful, ``scgen`` will create ``sproutcore`` folder in your current working directory with the auto-generated models inside of it.

Available options
-----------------
The ``scgen`` command has a number of useful options for specifying exactly what models to generate and where to generate them.

