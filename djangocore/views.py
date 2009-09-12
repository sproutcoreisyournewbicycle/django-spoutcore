from djangocore.utils import ajax_required, GET_required
from django.db.models import get_model

# TODO: Serialize the returned objects into valid JSON
# Right now none of these views will work as they are.

class ModelLengthFetcher(object):
    """
    Class that gets the count of a model.
    """
    
    @ajax_required
    @GET_required
    def __call__(request):
        data = request.GET.copy()
        model = get_model(*data['model'].split('.', 1))
        
        qs = self.get_queryset(request, model)
        return qs.count()
    
    def get_queryset(self, request, model):
        return model._default_manager.all()
        
class ModelRangeFetcher(object):
    """
    Class that fetches models in a range.
    """
    
    @ajax_required
    @GET_required
    def __call__(request):
        data = request.GET.copy()
        model = get_model(*data['model'].split('.', 1))
        ordering = data.get('ordering', 'pk').split(',')
        start = data.get('strat', None)
        end = data.get('end', None)
        
        qs = self.get_queryset(request, model, ordering, start, end)
        return qs
    
    def get_queryset(self, request, model, ordering, start, end):
        qs = model._default_manager.order_by(*ordering)
        
        if start and end:
            qs = qs[start:end]
        elif start:
            qs = qs[start:]
        elif end:
            qs = qs[:end]
        
        return qs

class ModelObjectFetcher(object):
    """
    Class that fetches models in a range.
    """
    
    @ajax_required
    @GET_required
    def __call__(request):
        data = request.GET.copy()
        model = get_model(*data['model'].split('.', 1))
        pks = data['pk'].split(',')

        qs = self.get_queryset(request, model, pks)
        return qs
    
    def get_queryset(self, request, model, pks):
        return model._default_manager.get(pk__in=pks)

