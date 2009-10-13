# Django dependencies.
from django.db.models.fields import NOT_PROVIDED
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson

# Intra-app dependencies.
from djangocore.utils import camelize, lcamelize, deconstruct


class BaseFieldTransformer(object):
    """Renders a Django model field as a SproutCore model field."""
    def __init__(self, field, acceptable_type='', extra_attributes=[], \
      reverse=False):
        super(BaseFieldTransformer, self).__init__()
        self.field = field
        self.acceptable_type = acceptable_type
        self.extra_attributes = extra_attributes
        self.reverse = reverse
            
    def should_render(self):
        raise NotImplementedError

    def get_name(self):
        raise NotImplementedError

    def get_js_type(self):
        raise NotImplementedError

    def get_attributes(self):
        """Subclasses should override this. Usually constructs an
        attribute list and then calls ``get_field_attrs_for``."""
        NotImplementedError

    def get_acceptable_type(self):
        """Override to compute acceptable types at runtime."""
        return self.acceptable_type

    def get_comments(self):
        return ['@type %s' % self.get_acceptable_type()]
    
    def get_record(self):
        return 'SC.Record.attr'

    def get_field_attrs_for(self, li):
        """Helper function to get the specified field attributes."""
        attributes_dict = {}
        
        # Loop over the list to find corresponding Python and SproutCore
        # attribute names.
        for l in li:
            if not hasattr(l, '__iter__'):
                l = [l]
                
            if len(l) == 1:
                pyname, scname = l[0], lcamelize(l[0])
                ignore = NOT_PROVIDED
            elif len(l) == 2:
                pyname, scname = l[0], l[1]
                ignore = NOT_PROVIDED
            elif len(l) == 3:
                pyname, scname, ignore = l[0], l[1], l[2]
        
            # Get the attribute's value, ignoring it if it doesn't exist or is
            # equal to the provided ignore value.
            try:
                attr = getattr(self.field, pyname)
                if callable(attr):
                    attr = attr()
                if attr != ignore:
                    attributes_dict[scname] = attr
            except AttributeError:
                print "%s has no attribute named '%s'" % (self.field, pyname)
            except TypeError, e:
                print "Unabled to call method '%s' on %s: %s" % \
                  (pyname, self.field, e)
            except:
                print "An error occurred while attempting to get the value " \
                 "for '%s' on %s" % (pyname, self.field)

        attributes_dict.update(
            # Add in the name of the actual field class
            fieldClass = self.field.__class__.__name__,
        )
        
        return attributes_dict
            
    def get_field_data(self):
        if self.should_render():
            return {
                'comments': '\n\n'.join(self.get_comments()),
                'name': self.get_name(),
                'record': self.get_record(),
                'js_type': self.get_js_type(),
                'attributes': simplejson.dumps(
                    deconstruct(self.get_attributes()),
                    cls = DjangoJSONEncoder,
                    ensure_ascii = False
                )
            }

class BaseModelTransformer(object):
    def __init__(self):
        super(BaseModelTransformer, self).__init__()
        self._transformations = {}
        self._reverse_transformations = {}
    
    def get_default_transformation(self):
        raise NotImplementedError

    def register(self, field_name, acceptable_type='', extra_attributes=[], \
      transformation=None):
        if transformation is None:
            transformation = self.get_default_transformation()
        self._transformations[field_name] = \
          (transformation, acceptable_type, extra_attributes)
    
    def register_reverse(self, field_name, acceptable_type='', \
      extra_attributes=[], transformation=None):
        if transformation is None:
            transformation = self.get_default_transformation()
        self._reverse_transformations[field_name] = \
          (transformation, acceptable_type, extra_attributes)

    def unregister(self, field_name):
        del self._transformations[field_name]
          
    def unregister_reverse(self, field_name):
        del self._reverse_transformations[field_name]

    def get_forward_fields(self, model):
        raise NotImplementedError

    def transform_forward_fields(self, model):
        fields = []
        for field in self.get_forward_fields(model):
            field_name = field.__class__.__name__
            try:
                Transformer, acceptable_type, extra_attributes \
                  = self._transformations[field_name]
            except KeyError:
                pass # Got a custom field type, so we punt on it.
            else:                
                t = Transformer(field, acceptable_type, \
                  extra_attributes).get_field_data()
                if t: fields.append(t)
        return fields
    
    def get_reverse_fields(self, model):
        raise NotImplementedError

    def transform_reverse_fields(self, model):
        fields = []
        for field in self.get_reverse_fields(model):
            field_name = field.__class__.__name__
            try:
                Transformer, acceptable_type, extra_attributes \
                  = self._reverse_transformations[field_name]
            except KeyError:
                pass # Got a custom field type, so we punt on it.
            else:                
                t = Transformer(field, acceptable_type, \
                  extra_attributes, reverse=True).get_field_data()
                if t: fields.append(t)
        return fields

    def generate_fields(self, model):
        return self.transform_forward_fields(model) + \
          self.transform_reverse_fields(model)
                
    def get_meta(self, model):
        raise NotImplementedError
    
    # rename to generate_scmodel_for()
    def get_model_data(self, model): 
        return {
            'generated_fields': self.generate_fields(model),
            'meta': [{'key': k, 'value': simplejson.dumps(deconstruct(v),
                cls=DjangoJSONEncoder, ensure_ascii=False)} for k, v in
                self.get_meta(model).items()],
        }
