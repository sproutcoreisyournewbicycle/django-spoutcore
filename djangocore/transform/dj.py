# Django dependencies.
from django.utils.encoding import smart_str

# Intra-app dependencies.
from djangocore.utils import camelize, lcamelize
from djangocore.transform.base import BaseFieldTransformer, \
  BaseModelTransformer

class DjangoFieldTransformer(BaseFieldTransformer):
    """Renders a Django model field as a SproutCore model field."""            
    def should_render(self):
        return not self.field.primary_key

    def get_name(self):
        return lcamelize(self.field.verbose_name) or \
          lcamelize(self.field.name)

    def get_js_type(self):
        return 'Django.%s' % self.field.__class__.__name__

    def get_attributes(self):
        attributes = [
            # python attr name      # sproutcore name
            ('name',                'key'),
            ('editable',            'isEditable'),
            ('default',             'defaultValue'),
            ('db_index',            'hasServerIndex'),
            ('verbose_name',        'verboseName'),
            
            # python attr name      # sproutcore name   # value to ignore
            ('unique',              'unique',           None),
            ('unique_for_date',     'uniqueForDate',    None),
            ('unique_for_month',    'uniqueForMonth',   None),
            ('unique_for_year',     'uniqueForYear',    None),
            ('choices',             'choices',          []),
        ]
        
        attributes.extend(self.extra_attributes)
        attributes_dict = self.get_field_attrs_for(attributes)
        attributes_dict.update(
            isRequired = not self.field.blank,
        )
        return attributes_dict

    def get_comments(self):
        comment_list = super(DjangoFieldTransformer, self).get_comments()
        if self.field.help_text:
            comment_list += [smart_str(self.field.help_text)]
        return comment_list
    
class DjangoRelationshipTransformer(DjangoFieldTransformer):
    def get_related_obj(self):
        if self.reverse:
            # We are looking at the reverse side of the relationship, so we want
            # to get the model the field is declared on.
            ops = self.field.related.model._meta
        
        else:
            # We are looking at the front side of the relationship, so we want
            # the model the field is related to.
            ops = self.field.related.parent_model._meta
        
        app_label = camelize(ops.app_label)
        module_name = camelize(ops.verbose_name)
        return '.'.join([app_label, module_name])
        
    def get_js_type(self):
        return r"'" + self.get_related_obj() + r"'"

    def get_name(self):
        if self.reverse:
            # Get the camlized related_name for the field, since there is no
            # field name to use from the reverse side of the relationship.
            return lcamelize(self.field.related.get_accessor_name())
        
        return super(DjangoRelationshipTransformer, self).get_name()
        
    def get_attributes(self):
        if self.reverse:
            attributes = self.extra_attributes
            attributes_dict = self.get_field_attrs_for(attributes)
            attributes_dict.update(
                isMaster = False,
                key = self.field.related.get_accessor_name(),
                inverse = lcamelize(self.field.verbose_name) or \
                  lcamelize(self.field.name),
            )
            
        else:
            attributes_dict = \
              super(DjangoRelationshipTransformer, self).get_attributes()

            attributes_dict.update(
                isMaster = True,
                inverse = lcamelize(self.field.related.get_accessor_name()),
            )
        
        return attributes_dict

class DjangoToOneTransformer(DjangoRelationshipTransformer):
    def get_acceptable_type(self):
        return self.get_related_obj()
    def get_record(self):
        return 'SC.Record.toOne'
    
class DjangoToManyTransformer(DjangoRelationshipTransformer):
    def get_acceptable_type(self):
        return 'SC.RecordArray %s' % self.get_related_obj()
    def get_record(self):
        return 'SC.Record.toMany'

class DjangoModelTransformer(BaseModelTransformer):
    def get_default_transformation(self):
        return DjangoFieldTransformer

    def get_forward_fields(self, model):
        ops = model._meta
        return ops.fields + ops.many_to_many
    
    def get_reverse_fields(self, model):
        ops = model._meta
        return [obj.field for obj in ops.get_all_related_objects()] + \
          [obj.field for obj in ops.get_all_related_many_to_many_objects()]

    def get_meta(self, model):
        ops = model._meta
        meta_dict= dict(
            transformedFrom = 'Django',
            modelClass = '.'.join([ops.app_label, ops.module_name]),
            verboseName = ops.verbose_name.title(),
            verboseNamePlural = ops.verbose_name_plural.title(),
        )

        attributes = [
            'get_latest_by',
            'ordering',
            'order_with_respect_to',
            'unique_together',
        ]
        
        for attr in attributes:
            value = getattr(ops, attr, None)
            if value is not None:
                meta_dict[lcamelize(attr)] = value
        
        return meta_dict

transformer = DjangoModelTransformer()

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
transformer.register('AutoField', 'Integer')
transformer.register('SmallIntegerField', 'Integer')
transformer.register('IntegerField', 'Integer')
transformer.register('PositiveIntegerField', 'Positive integer')
transformer.register('PositiveSmallIntegerField', 'Positive integer')
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
transformer.register('OneToOneField', transformation=DjangoToOneTransformer)
transformer.register('ForeignKey', transformation=DjangoToOneTransformer)
transformer.register('ManyToManyField', transformation=DjangoToManyTransformer)
transformer.register_reverse('ForeignKey', transformation=DjangoToManyTransformer)
transformer.register_reverse('ManyToManyField', \
  transformation=DjangoToManyTransformer)
transformer.register_reverse('OneToOneField', \
  transformation=DjangoToOneTransformer)
