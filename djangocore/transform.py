# Django dependencies.
from django.db.models.fields import NOT_PROVIDED
from django.utils.encoding import smart_str
from django.template.loader import render_to_string

# Intra-app dependencies.
from djangocore.utils import camelize, lcamelize, SproutCoreJSONEncoder

json = SproutCoreJSONEncoder()

class BaseTransformation(object):
    """Renders a Django model field as a SproutCore model field."""
    def __init__(self, field, acceptable_type='', extra_attributes=[], reverse=False):
        super(BaseTransformation, self).__init__()
        self.field = field
        self.acceptable_type = acceptable_type
        self.extra_attributes = extra_attributes
        self.reverse = reverse
            
    def should_render(self):
        return not self.field.primary_key

    def get_acceptable_type(self):
        """
        Returns a list of acceptable javascript types for this
        sproutcore field. Only used for documentation purposes.
        
        Can be overriden by subclasses to compute acceptable types at
        runtime.
        
        """
        return self.acceptable_type

    def get_comments(self):
        comment_list = ['@type %s' % self.get_acceptable_type()]

        if self.field.help_text:
            comment_list += [smart_str(self.field.help_text)]
        return comment_list
    
    def get_name(self):
        # If the verbose name is an empty string, we fall back to the field
        # name.
        return lcamelize(self.field.verbose_name) or \
          lcamelize(self.field.name)

    def get_record(self):
        return 'SC.Record.attr'

    def get_js_type(self):
        return 'Django.%s' % self.field.__class__.__name__

    def get_attributes(self):
        # These values are common to all (built-in) fields.
        attribute_dict = {
            'key': self.field.name,
            'isRequired': self.field.blank,
            'isEditable': self.field.editable,
            'unique': self.field.unique,
            'djangoField': self.field.__class__.__name__,
        }
        
        # Some values we only want to include if they've been set by the user.
        for key, value in {
            'uniqueForDate': self.field.unique_for_date,
            'uniqueForMonth': self.field.unique_for_month,
            'uniqueForYear': self.field.unique_for_year,
        }.items():
            if value is not None:
                attribute_dict[key] = value
        
        # FYI: Django uses a special NOT_PROVIDED class to differentiate between
        # a user setting default=None and no default being set.
        if self.field.default != NOT_PROVIDED:
            attribute_dict['defaultValue'] = self.field.default
            
        # If the transformation was given any extra attributes to look for on
        # the field, we add them to attributes_dict.
        for attr in self.extra_attributes:
            # If the attribute is a single string, we camelize it for the key.
            if isinstance(attr, str):
                key = lcamelize(attr)
                value = attr
            
            # If the attribute is a 2-value tuple, then we upack the key.
            elif (isinstance(attr, list) or isinstance(attr, tuple)) and \
              len(attr) == 2:
                key, value = attr

            # If the attribute is not in a form we recognize, we skip it.
            else:
                continue
            
            attribute_dict[key] = getattr(self.field, value, None)
            
        return attribute_dict

    def get_field_data(self):
        if self.should_render():
#            try:
                return {
                    'comments': '\n\n'.join(self.get_comments()),
                    'name': self.get_name(),
                    'record': self.get_record(),
                    'js_type': self.get_js_type(),
                    'attributes': json.encode(self.get_attributes())
                }
#            except:
#                # There was some error with the field, so we punt on it rather than
#                # crash the whole process.
#                pass

class BaseRelationshipTransformation(BaseTransformation):
    def get_related_obj(self):
        # If we are looking at the reverse side of the relationship, then we
        # want to get the model the field is declared on.
        if self.reverse:
            ops = self.field.related.model._meta
        
        # If we are looking at the front side of the relationship though, we
        # want the model the field is related to.
        else:
            ops = self.field.related.parent_model._meta
        
        app_label, model_name = camelize(ops.app_label), camelize(ops.verbose_name)
        return '.'.join([app_label, model_name])
        
    def get_js_type(self):
        return r"'" + self.get_related_obj() + r"'"

    def get_name(self):
        if self.reverse:
            # Get the camlized related_name for the field, since there is no
            # field name to use.
            return lcamelize(self.field.related.get_accessor_name())
        
        return super(BaseRelationshipTransformation, self).get_name()
        
    def get_attributes(self):
        if self.reverse:
            # Since this is the reverse side of a relationship, it doesn't make
            # sense to have a lot of the attributes we normally use for a field.
            attributes_dict = {
                'djangoField': self.field.__class__.__name__,
                'isMaster': False,
                'key': self.field.related.get_accessor_name(),
                'inverse': lcamelize(self.field.verbose_name) or \
                  lcamelize(self.field.name),
            }
        else:
            attributes_dict = \
              super(BaseRelationshipTransformation, self).get_attributes()

            attributes_dict.update({
                'isMaster': not self.reverse,
                'inverse': lcamelize(self.field.related.get_accessor_name()),
            })
        
        return attributes_dict

class ToOneTransformation(BaseRelationshipTransformation):
    def get_acceptable_type(self):
        return self.get_related_obj()
    def get_record(self):
        return 'SC.Record.toOne'
    
class ToManyTransformation(BaseRelationshipTransformation):
    def get_acceptable_type(self):
        return 'SC.RecordArray %s' % self.get_related_obj()
    def get_record(self):
        return 'SC.Record.toMany'

class ModelTransformer(object):
    def __init__(self):
        super(ModelTransformer, self).__init__()
        self._transformations = {}
        self._reverse_transformations = {}
    
    def register(self, field_name, acceptable_type='', extra_attributes=[], \
      transformation=BaseTransformation):
        self._transformations[field_name] = \
          (transformation, acceptable_type, extra_attributes)
    
    # We don't accept any extra_attributes since it usually doesn't make sense
    # to put them on the reverse model's field.
    def register_reverse(self, field_name, acceptable_type='', \
      transformation=BaseTransformation):
        self._reverse_transformations[field_name] = \
          (transformation, acceptable_type)

    def unregister(self, field_name):
        del self._transformations[field_name]
          
    def unregister_reverse(self, field_name):
        del self._reverse_transformations[field_name]

    def get_fields(self, model):
        fields = []
        ops = model._meta
        
        # Regular fields and forward relationships
        for field in ops.fields + ops.many_to_many:
            try:
                field_name = field.__class__.__name__
                Transformation, acceptable_type, extra_attributes \
                  = self._transformations[field_name]
                
                t = Transformation(field, acceptable_type, \
                  extra_attributes).get_field_data()
                if t: fields.append(t)
            except KeyError:
                # Got a custom field type, so we punt on it.
                pass
                
        # Reverse relationships
        reverse_fields = [obj.field for obj in ops.get_all_related_objects()] + \
          [obj.field for obj in ops.get_all_related_many_to_many_objects()]
        for field in reverse_fields:
            try:
                field_name = field.__class__.__name__
                Transformation, acceptable_type \
                  = self._reverse_transformations[field_name]
                
                t = Transformation(field, acceptable_type, \
                  [], reverse=True).get_field_data()
                if t: fields.append(t)
            except KeyError:
                # Got a custom field type, so we punt on it.
                pass
        
        return fields
        
    def get_meta(self, model):
        ops = model._meta
        meta_dict = {
            'djangoModel': '.'.join([ops.app_label, ops.module_name]),
            'verboseName': ops.verbose_name,
            'verboseNamePlural': ops.verbose_name_plural,
        }
        
        for key, value in {
            'getLatestBy': ops.get_latest_by,
            'ordering': ops.ordering,
            'orderWithRespectTo': ops.order_with_respect_to,
            'uniqueTogether': ops.unique_together,
        }.items():
            if value:
                meta_dict[key] = value

        return [{'name': key , 'value': json.encode(value)} for \
          key, value in meta_dict.items()]
        
    def get_model_data(self, model): 
#        try:
            return {
                'generated_fields': self.get_fields(model),
                'meta': self.get_meta(model),
            }
#        except:
#            # There was some error with the model, so we punt on it rather than
#            # crash the whole process.
#            pass

transformer = ModelTransformer()

# String fields
transformer.register('TextField', 'String')
transformer.register('CharField', 'String', ('max_length',))
transformer.register('EmailField', 'String', ('max_length',))
transformer.register('SlugField', 'String', ('max_length',))
transformer.register('IPAddressField', 'String', ('max_length',))
transformer.register('URLField', 'String', ('verify_exists',))
transformer.register('XMLField', 'String', ('max_length', 'schema_path',))
transformer.register('CommaSeparatedIntegerField', \
  'String of comma-separated integers', ('max_length',))
transformer.register('FileField', 'String', ('max_length', 'upload_to',))
transformer.register('ImageField', 'String', ('max_length', 'upload_to', \
  'height_field', 'width_field',))
transformer.register('FilePathField', 'String', ('max_length', 'path', \
  'match', 'recursive',))

# Number fields
transformer.register('AutoField', 'Number')
transformer.register('SmallIntegerField', 'Number')
transformer.register('IntegerField', 'Number')
transformer.register('PositiveIntegerField', 'Number')
transformer.register('PositiveSmallIntegerField', 'Number')
transformer.register('FloatField', 'Number')
transformer.register('DecimalField', 'Number', ('max_digits', 'decimal_places',))

# Date fields
transformer.register('DateField', 'Date', ('auto_now', 'auto_now_add',))
transformer.register('DateTimeField', 'Date', ('auto_now', 'auto_now_add',))
transformer.register('TimeField', 'Date', ('auto_now', 'auto_now_add',))

# Boolean fields
transformer.register('NullBooleanField', 'Boolean')
transformer.register('BooleanField', 'Boolean')

# Relationship fields
transformer.register('OneToOneField', transformation=ToOneTransformation)
transformer.register('ForeignKey', transformation=ToOneTransformation)
transformer.register('ManyToManyField', transformation=ToManyTransformation)
transformer.register_reverse('ForeignKey', transformation=ToManyTransformation)
transformer.register_reverse('ManyToManyField', \
  transformation=ToManyTransformation)
transformer.register_reverse('OneToOneField', \
  transformation=ToOneTransformation)
