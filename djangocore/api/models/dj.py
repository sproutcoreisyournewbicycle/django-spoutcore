# Django dependencies.
from django.core.exceptions import FieldError
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.forms.models import modelform_factory

# Intra-app dependencies.
from djangocore.api.models.base import BaseModelResource
from djangocore.serialization import emitter, EmittableResponse

class DjangoModelResource(BaseModelResource):
    allow_related_ordering = False # Allow ordering across relationships.
    user_field_name = None # The field to filter on the current user.
                           # Only logged in users get filtered responses.
    
    def __init__(self, *args, **kwargs):
        super(DjangoModelResource, self).__init__(*args, **kwargs)
        
        # Construct a default form if we don't have one already.
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
        
        if isinstance(response, QuerySet):
            response = self.serialize_models(response)
        
        # TODO: how do we catch bad format requests?
        format = request.GET.get('format', 'json')
        response = emitter.translate(format, response)
        return response

    def process_lookups(self, lookups):
        """
        GET parameter keys are unicode strings, but we can only pass in
        strings as keyword arguments, so we convert them here.
        
        """
        return dict([(str(k), v) for k, v in lookups.items()])

    def get_query_set(self, request):
        qs = self.model._default_manager.all()
        if self.user_field_name and hasattr(request.user, 'pk'):
            lookups = {}
            lookups[user_field_name] = request.user
            qs = qs.filter(**lookups)
        return qs

    def length(self, request):
        lookups = request.GET.copy()

        qs = self.get_query_set(request)
        
        try:
            qs = qs.filter(**self.process_lookups(lookups))
        except FieldError, err:
            return EmittableResponse(str(err), status=400)
        
        return qs.count()

    def list(self, request):
        lookups = request.GET.copy()

        qs = self.get_query_set(request)

        ordering = lookups.pop('ordering', None)
        if ordering:
            if not self.allow_related_ordering and '__' in ordering:
                return EmittableResponse("This model cannot be ordered by "
                    "related objects. Please remove all ocurrences of '__' from"
                    " your ordering parameters.", status=400)
            
            ordering = ordering.split(',')            
            if len(ordering) > self.max_orderings:
                return EmittableResponse("This model cannot be ordered by more "
                    "than %d parameter(s). You tried to order by %d parameters."
                    % (self.max_orderings, len(ordering)), status=400)
            
            qs = qs.order_by(*ordering)

        offset = lookups.pop('offset', 0)
        limit = min(lookups.pop('limit', self.max_objects), self.max_objects)
        
        try:
            # Catch any lookup errors, and return the message, since they are
            # usually quite descriptive.
            qs = qs.filter(**self.process_lookups(lookups))
        except FieldError, err:
            return EmittableResponse(str(err), status=400)
        
        return qs[offset:offset + limit]

    def show(self, request):
        pk_list = request.GET.getlist('pk')
        
        if len(pk_list) == 0:
            return EmittableResponse("The request must specify a pk argument",
                status=400)
                    
        qs = self.get_query_set(request)
        return qs.filter(pk__in=pk_list)    

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
        pk = pk_list[0]
                
        # Make sure the data we recieved is in the right format.
        data = request.data                
        if not isinstance(data, dict):
            return EmmitableResponse("The data sent in the request was "
                "malformed", status=400)
        
        instance = get_object_or_404(self.get_query_set(request), pk=pk)

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
        
        qs = self.get_query_set(request)
        
        # QUESTION: Should we delete in bulk or loop through and delete?
        qs.filter(pk__in=pk_list).delete()
        
        return HttpResponse('', status=204)    

# Alias to make importing easier, while retaining the class's full name.
ModelResource = DjangoModelResource