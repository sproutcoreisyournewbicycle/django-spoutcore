# Django dependencies.
from django.core.serializers import serialize
from django.conf.urls.defaults import patterns, url, include

# Intra-app dependencies.
from djangocore.api.resources import BaseResource
from djangocore.transform.forms import transformer

class BaseModelResource(BaseResource):
    max_orderings = 1 # max number of order parameters for a query
    max_objects = 100 # max number of objects returned by a query
    
    model = None
    form = None # a model form class to use when creating and updating objects
    fields = () # the fields to expose when serializing this model
    
    def __init__(self, *args, **kwargs):
        super(BaseModelResource, self).__init__(*args, **kwargs)
        
        # Throw an error if the developer forgot to set a model on the Resource
        if not self.model:
            raise TypeError("%s must specify a model attribute" %
                self.__class__.__name__)

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url
        urlpatterns = patterns('',
            url('^length/$',    self.mapper,    self.ops(get='length')),
            url('^list/$',      self.mapper,    self.ops(get='list')),
            url('^form/$',      self.mapper,    self.ops(get='form')),
            url('^$',           self.mapper,    self.ops(get='show', \
              post='create', put='update', delete='destroy')),
        )
        return urlpatterns

    def get_url_prefix(self):
        ops = self.model._meta
        return 'models/%s/%s/' % (ops.app_label, ops.module_name)

    def serialize_models(self, model_or_iterable):
        """
        Convert a model (or list of models) into standard python types
        for later serialization.
        
        """
        iterable = True
        if not hasattr(model_or_iterable, '__iter__'):
            model_or_iterable = [model_or_iterable]
            iterable = False

        if self.fields:
            # Filter the model's fields, if the resource requires it.
            s = serialize('python', model_or_iterable, fields=self.fields)
        else:
            s = serialize('python', model_or_iterable)
        
        # If we were given a single item, then we return a single item.
        if iterable == False:
            s = s[0]
        return s

    def get_query_set(self, request):
        return self.model._default_manager.all()
    
    def length(self, request):
        raise NotImplementedError

    def list(self, request):
        raise NotImplementedError

    def meta(self, request):
        return transformer.render(self.form)

    def show(self, request):
        raise NotImplementedError

    def create(self, request):
        raise NotImplementedError

    def update(self, request):
        raise NotImplementedError

    def destroy(self, request):
        raise NotImplementedError
