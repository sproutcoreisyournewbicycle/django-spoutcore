# Django dependencies.
from django.utils.encoding import smart_str

# Intra-app dependencies.
from djangocore.utils import camelize, lcamelize, splitwords
from djangocore.transform.base import BaseFieldTransformer, \
  BaseModelTransformer



class AppEngineFieldTransformer(BaseFieldTransformer):
    """Renders a AppEngine model field as a SproutCore model field."""            
    def should_render(self):
        return True

    def get_name(self):
        return lcamelize(getattr(self.field, 'verbose_name', '')) or \
          lcamelize(self.field.name)

    def get_js_type(self):
        return 'AppEngine.%s' % self.field.__class__.__name__

    def get_attributes(self):
        attributes = [
            # python attr name  # sproutcore name
            ('name',            'key'),
            ('required',        'isRequired'),
            ('indexed',         'hasServerIndex'),
            
            # python attr name  # sproutcore name   # value to ignore
            ('choices',         'choices',          None),
            ('default',         'defaultValue',     None),
            ('verbose_name',    'verboseName',      None),
        ]
        
        attributes.extend(self.extra_attributes)
        attributes_dict = self.get_field_attrs_for(attributes)
        return attributes_dict

class AppEngineUnindexedFieldTransformer(AppEngineFieldTransformer):
    """
    Some of App Engine's fields can't be indexed, but they still set
    their indexed attribute to True, so we use a special field
    transformation that always sets ``hasServerIndex`` to False.
    
    """
    def get_attributes(self):
        attributes_dict = super(AppEngineUnindexedFieldTransformer, self).get_attributes()
        attributes_dict.update(
            hasServerIndex = False,
        )
        return attributes_dict
    
class AppEngineRelationshipTransformer(AppEngineFieldTransformer):
    def get_acceptable_type(self):
        if self.reverse:
            return 'SC.RecordArray %s' % self.get_related_obj()
        return self.get_related_obj()
    
    def get_record(self):
        if self.reverse:
            return 'SC.Record.toMany'
        return 'SC.Record.toOne'

    def get_related_obj(self):
        if self.reverse:
            # We are looking at the reverse side of the relationship, so we want
            # to get the model the field is declared on.
            ops = self.field._model._meta
        
        else:
            # We are looking at the front side of the relationship, so we want
            # the model the field is related to.
            ops = self.field.reference_class._meta
        
        app_label = camelize(ops.app_label)
        module_name = camelize(ops.module_name)
        return '.'.join([app_label, module_name])
        
    def get_js_type(self):
        return r"'" + self.get_related_obj() + r"'"

    def get_name(self):
        if self.reverse:
            # Grab the ReferenceProperty field on the related model.
            related_field = getattr(self.field._model, self.field._prop_name)
            return lcamelize(related_field.collection_name)
        
        return super(AppEngineRelationshipTransformer, self).get_name()
        
    def get_attributes(self):
        if self.reverse:
            attributes = self.extra_attributes
            attributes_dict = self.get_field_attrs_for(attributes)
            
            # Grab the ReferenceProperty field on the related model so that
            # we can figureout what the inverse field name should be.
            related_field = getattr(self.field._model, self.field._prop_name)
            attributes_dict.update(
                isMaster = False,
                key = related_field.collection_name,
                inverse = lcamelize(getattr(related_field, \
                  'verbose_name', '')) or lcamelize(related_field.name),
            )
            
        else:
            attributes_dict = \
              super(AppEngineRelationshipTransformer, self).get_attributes()

            attributes_dict.update(
                isMaster = True,
                inverse = lcamelize(self.field.collection_name),
            )
        
        return attributes_dict

class AppEngineModelTransformer(BaseModelTransformer):
    def get_default_transformation(self):
        return AppEngineFieldTransformer

    def get_forward_fields(self, model):
        return model._meta.local_fields
    
    def transform_reverse_fields(self, model):
        fields = []
        
        # Get a list of all the forward field names, so we can check against it.
        forward_field_names = [f.name for f in self.get_forward_fields(model)]
        
        # AppEngine doesn't bother to store any metadata about reverse
        # properties, so we need to loop over *every* attribute on the model
        # looking for _ReverseReferenceProperty classes. Pain. In. The. Ass...
        for name in dir(model):
            field = getattr(model, name)
            field_name = field.__class__.__name__
            
            # Make sure we haven't already seen the field in the forward lookup.
            if name not in forward_field_names and \
              field_name in self._reverse_transformations :
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

    def get_meta(self, model):
        ops = model._meta

        meta_dict = dict(
            transformedFrom = 'AppEngine',
            modelClass = '.'.join([ops.app_label, ops.module_name]),
            verboseName = splitwords(ops.object_name).title(),
        )
        
        return meta_dict

transformer = AppEngineModelTransformer()

# String fields
transformer.register('StringProperty', 'String', ('multiline',))
transformer.register('UserProperty', 'String', ('auto_current_user', 'auto_current_user_add'))
transformer.register('CategoryProperty', 'String')
transformer.register('EmailProperty', 'String')
transformer.register('LinkProperty', 'String (fully qualified URL)')
transformer.register('PhoneNumberProperty', 'String')
transformer.register('PostalAddressProperty', 'String')
transformer.register('GeoPtProperty', 'String (latitude, longitude)')
transformer.register('IMProperty', 'String (protocol, handle)')
transformer.register('TextProperty', 'String', transformation=AppEngineUnindexedFieldTransformer)

# Number fields
transformer.register('FloatProperty', 'Number')
transformer.register('IntegerProperty', 'Number')
transformer.register('RatingProperty', 'Integer (0-100)')

# Date fields
transformer.register('DateProperty', 'Date', ('auto_now', 'auto_now_add'))
transformer.register('DateTimeProperty', 'Date', ('auto_now', 'auto_now_add'))
transformer.register('TimeProperty', 'Date', ('auto_now', 'auto_now_add'))

# Bolean fields
transformer.register('BooleanProperty', 'Boolean')

# Array fields
transformer.register('StringListProperty', 'Array of Strings')
transformer.register('ByteStringProperty', 'Array of integers (0-255)')
transformer.register('ListProperty', 'Array of %s') # TODO: !!! VARIES !!!
transformer.register('BlobProperty', 'Array of integers (0-255)', \
  transformation=AppEngineUnindexedFieldTransformer)

# Relationship fields
transformer.register('ReferenceProperty', transformation=AppEngineRelationshipTransformer)
transformer.register('SelfReferenceProperty', transformation=AppEngineRelationshipTransformer)
transformer.register_reverse('_ReverseReferenceProperty', \
  transformation=AppEngineRelationshipTransformer)
