# Google dependencies.
from google.appengine.ext.db import Key, PropertyError, Query
from google.appengine.ext.db.djangoforms import ModelForm, ModelFormMetaclass

# Django dependencies.
from django.http import HttpResponse, HttpResponseBadRequest

# Intra-app dependencies.
from djangocore.api.models.base import BaseModelResource
from djangocore.serialization import emitter, EmittableResponse

def modelform_factory(model, form=ModelForm, fields=None, exclude=None,
                       formfield_callback=lambda f: f.formfield()):
    """
    Copied out of `django.forms.models`, since we have to use
    AppEngine's ModelFormMetaclass in order to create functioning forms.
    
    """
    # Create the inner Meta class. FIXME: ideally, we should be able to
    # construct a ModelForm without creating and passing in a temporary
    # inner class.

    # Build up a list of attributes that the Meta object will have.
    attrs = {'model': model}
    if fields is not None:
        attrs['fields'] = fields
    if exclude is not None:
        attrs['exclude'] = exclude

    # If parent form class already has an inner Meta, the Meta we're
    # creating needs to inherit from the parent's inner meta.
    parent = (object,)
    if hasattr(form, 'Meta'):
        parent = (form.Meta, object)
    Meta = type('Meta', parent, attrs)

    # Give this new form class a reasonable name.
    class_name = model.__name__ + 'Form'

    # Class attributes for the new form class.
    form_class_attrs = {
        'Meta': Meta,
        'formfield_callback': formfield_callback
    }

    return ModelFormMetaclass(class_name, (form,), form_class_attrs)

class AppEngineModelResource(BaseModelResource):    
    # TODO: Find out if =, !=, and IN are case-sensitive or not...
    lookup_delimiter = '__'
    lookup_mapper = {
        'exact': '=',
        'lt': '<',
        'lte': '<=',
        'gte': '>=',
        'gt': '>',
        'not': '!=',
        'in': 'IN',
    }

    def __init__(self, *args, **kwargs):
        super(AppEngineModelResource, self).__init__(*args, **kwargs)
        
        if not self.form:
            if self.fields:
                # Limit it to the specified fields, if given.
                self.form = modelform_factory(self.model, fields=self.fields)
            else:
                self.form = modelform_factory(self.model)
                
    def process_response(self, response, request):
        """
        Process the response and serialize any returned data structures.
        
        """
        if isinstance(response, HttpResponse):
            return response
        
        if isinstance(response, Query):
            response = self.serialize_models(response)

        # TODO: how do we catch bad format requests?
        format = request.GET.get('format', 'json')
        response = emitter.translate(format, response)
        return response

    def process_lookups(self, lookups):
        """
        Convert Django-style lookups to proper AppEngine lookups.
        
        """
        newlookups = {}
        for k, v in lookups.items():
            if '__' in k:
                l = k.rsplit(self.lookup_delimiter, 1)
                n = self.lookup_mapper.get(l[-1], '')
                k = '%s %s' % (l, n)
            newlookups[str(k)] = v
        return newlookups
    
    def length(self, request):
        lookups = request.GET.copy()
        max_count = lookups.pop('max', 0)

        qs = self.get_query_set(request).order('__key__')

        try:
            # Catch any lookup errors here and return them to the client.
            for k, v in self.process_lookups(lookups):
                qs = qs.filter(k, v)
        except PropertyError, err:
            return EmittableResponse(str(err), status=400)

        total_count = last_count = qs.count(1000)
        while last_count == 1000:
            # If the client specified a max count parameter, then we stop
            # cycling once we reach it.
            if max_count and total_count >= max_count:
                break

            # Get the next batch of objects to count.
            last_key = qs.fetch(1, 999).get()
            last_count = qs.filter("__key__ >", last_key).count(1000)
            total_count += last_count
            
        if max_count and total_count >= max_count:
            return max_count
            
        return total_count
    
    def list(self, request):
        lookups = request.GET.copy()

        qs = self.get_query_set(request)

        ordering = lookups.pop('ordering', None)
        if ordering:
            ordering = ordering.split(',')            
            if len(ordering) > self.max_orderings:
                return EmittableResponse("This model cannot be ordered by more "
                    "than %d parameter(s). You tried to order by %d parameters."
                    % (self.max_orderings, len(ordering)), status=400)
            
            for o in ordering:
                qs = qs.order(o)
            
        offset = lookups.pop('offset', 0)
        limit = min(lookups.pop('limit', self.max_objects), self.max_objects)
        
        try:
            # Catch any lookup errors here and return them to the client.
            for k, v in self.process_lookups(lookups):
                qs = qs.filter(k, v)
        except PropertyError, err:
            return EmittableResponse(str(err), status=400)
        
        return self.serialize_models(qs.fetch(limit, offset))
    
    def show(self, request):
        pk_list = request.GET.getlist('pk')
        
        if len(pk_list) == 0:
            return EmittableResponse("The request must specify a pk argument",
                status=400)
        
        # Turn the specified pks into Key objects for lookup.
        pk_list = [Key(pk) for pk in pk_list]
              
        qs = self.get_query_set(request)
        qs = qs.filter('__key__ IN', pk_list)
        return self.serialize_models(qs.fetch(self.max_objects))

    def create(self, request):
        data = request.data
        
        # Make sure the data we recieved is in the right format.
        if not isinstance(data, dict):
            return EmittbaleResponse("The data sent in the request was "
                "malformed", status=400)
        
        form = self.form(data)
        if form.errors:
            return EmittableResponse({'errors': form.errors}, status=400)
            
        obj = form.save()
        return self.serialize_models(obj)
    
    def update(self, request):
        pk_list = request.GET.getlist('pk')
        if len(pk_list) != 1:
            return EmittableResponse("The request must specify a single pk "
                "argument", status=400)
        key = Key(pk_list[0])

        # Make sure the data we recieved is in the right format.
        data = request.data                
        if not isinstance(data, dict):
            return EmmitableResponse("The data sent in the request was "
                "malformed", status=400)
        
        instance = self.get_query_set(request).filter('__key__ =', key).get()
        if not instance:
            raise Http404
        
        form = self.form(data, instance=instance)
        if form.errors:
            return EmittableResponse({'errors': form.errors}, status=400)
            
        obj = form.save()
        return self.serialize_models(obj)
    
    def destroy(self, request):
        pk_list = request.GET.getlist('pk')
        
        if len(pk_list) == 0:
            return EmittableResponse("The request must specify a pk argument",
                status=400)
        
        # Turn the specified pks into Key objects for lookup.
        pk_list = [Key(pk) for pk in pk_list]
              
        qs = self.get_query_set(request)
        qs = qs.filter('__key__ IN', pk_list)

        # If we got back a 1000 objects, we probably hit AppEngine's ceiling, so 
        # we delete them and repeat the query until we get everything.
        num = 1000
        while num == 1000:
            num = 0
            objects = qs.fetch(1000)
            for obj in objects:
                obj.delete()
                num += 1

        return HttpResponse('', status=204)    

# Alias to make importing easier, while retaining the class's full name.
ModelResource = AppEngineModelResource