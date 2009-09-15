# Django dependencies.
from django.db.models.fields import NOT_PROVIDED
from django.utils.simplejson import JSONEncoder
from django.utils.encoding import smart_str

# Intra-app dependencies.
from djangocore.utils import camelize

class Comments(list):
    """A list of comments that knows how to render itself."""
    def render(self):
        return '/**\n' + '\n\n'.join([str(s) for s in self]) + '\n*/'
    
    def __str__(self):
        return self.render()

# Add a default parameter to the JSONEncoder that will try to force any
# unserializable object to a string, rather than just throwing an error.
dumps = JSONEncoder(default=lambda o: smart_str(o, strings_only=True)).encode

class Attributes(dict):
    """A dictionary of attributes that knows how to render itself."""
    def render(self):
        return dumps(self)
    
    def __str__(self):
        return self.render()

class Field(object):
    """A sproutcore field that knows how to render itself."""
    def __init__(self, name, record, js_type, attributes, comments):
        super(Field, self).__init__()
        self.name = name
        self.record = record
        self.js_type = js_type
        self.attributes = attributes
        self.comments = comments
        
    def render(self):
        comments = self.comments.render()
        field = '%s: %s(%s)' % (
            self.name,
            self.record,
            ', '.join([self.js_type, self.attributes.render()])
        )
        return comments + '\n' + field

    def __str__(self):
        return self.render()

class ModelTransformer(object):
    def __init__(self):
        super(ModelTransformer, self).__init__()
        self._transformations = {}
        self._reverse_transformations = {}
    
    def register(self, field_name, transformation):
        self._transformations[field_name] = transformation
    def register_reverse(self, field_name, transformation):
        self._reverse_transformations[field_name] = transformation
    
    def render(self, model):
        fields = []
        ops = model._meta
        # Regular fields and forward relationships
        for field in ops.fields + ops.many_to_many:
            try:
                field_name = field.__class__.__name__
                f = self._transformations[field_name](field).render()
                if f: fields.append(f)
            except KeyError:
                # Got a custom field type, so we punt on it.
                pass
                
        # Reverse relationships
        reverse_fields = [obj.field for obj in ops.get_all_related_objects()] + \
            [obj.field for obj in ops.get_all_related_many_to_many_objects()]
        for field in reverse_fields:
            field_name = field.__class__.__name__
            f = self._reverse_transformations[field_name](field).render()
            if f: fields.append(f)
         
        return ',\n\n'.join(fields)
 
transformer = ModelTransformer()

class BaseFieldTransformation(object):
    def __init__(self, field):
        super(BaseFieldTransformation, self).__init__()
        self.field = field
        
    def get_name(self):
        name = camelize(smart_str(self.field.verbose_name))
        if name:
            return name[0].lower() + name[1:]

    def get_js_type(self):
        return 'Django.%s' % self.field.__class__.__name__
    
    def get_acceptable_types(self):
        raise NotImplementedError
        
    def get_record(self):
        return 'SC.Record.attr'

    def get_attributes(self):
        a = Attributes(dict(
            key = self.field.name,
            isRequired = self.field.blank,
            isEditable = self.field.editable,
            isUnique = self.field.unique,
            djangoField = self.field.__class__.__name__,
        ))
        
        # We only add these to the attributes if they are actually defined.
        uniques = dict(
            defaultValue = self.field.default,
            isUniqueForDate = self.field.unique_for_date,
            isUniqueForMonth = self.field.unique_for_month,
            isUniqueForYear = self.field.unique_for_year,
        )
        
        # Cycle through and add the ones with values.
        for key, value in uniques.items():
            if value != None and value != NOT_PROVIDED:
                a[key] = value

        return a
        
    def get_comments(self):
        c = Comments(['@type %s' % self.get_acceptable_types()])
        if self.field.help_text:
            c.insert(0, smart_str(self.field.help_text))
        return c
    
    def should_render(self):
        return not self.field.primary_key
    
    def render(self):
        if self.should_render():
            field = Field(
                name = self.get_name(),
                record = self.get_record(),
                js_type = self.get_js_type(),
                attributes = self.get_attributes(),
                comments = self.get_comments(),
            )
            return field.render()
    
    def __str__(self):
        return self.render()
        
# Text fields
class StringFieldTransformation(BaseFieldTransformation):
    def get_acceptable_types(self):
        return 'String'
transformer.register('TextField', StringFieldTransformation)
        
class CharFieldTransformation(StringFieldTransformation):
    def get_attributes(self):
        a = super(CharFieldTransformation, self).get_attributes()
        a.update(
            maxLength = self.field.max_length
        )
        return a
transformer.register('CharField', CharFieldTransformation)
transformer.register('EmailField', CharFieldTransformation)
transformer.register('SlugField', CharFieldTransformation)
transformer.register('IPAddressField', CharFieldTransformation)

class FileFieldTransformation(CharFieldTransformation):
    def get_attributes(self):
        a = super(FileFieldTransformation, self).get_attributes()
        a.update(
            uploadTo = self.field.upload_to
        )
        return a
transformer.register('FileField', FileFieldTransformation)

class ImageFieldTransformation(FileFieldTransformation):
    def get_attributes(self):
        a = super(ImageFieldTransformation, self).get_attributes()
        a.update(
            heightField = self.field.height_field,
            widthField = self.field.width_field
        )
        return a
transformer.register('ImageField', ImageFieldTransformation)

class FilePathFieldTransformation(CharFieldTransformation):
    def get_attributes(self):
        a = super(FilePathFieldTransformation, self).get_attributes()
        a.update(
            path = self.field.path,
            match = self.field.match,
            recursive = self.field.recursive,
        )
        return a
transformer.register('FilePathField', FilePathFieldTransformation)

class URLFieldTransformation(CharFieldTransformation):
    def get_attributes(self):
        a = super(URLFieldTransformation, self).get_attributes()
        a.update(
            verifyExists = self.field.verify_exists
        )
        return a
transformer.register('URLField', URLFieldTransformation)

class XMLFieldTransformation(CharFieldTransformation):
    def get_attributes(self):
        a = super(XMLFieldTransformation, self).get_attributes()
        a.update(
            schemaPath = self.field.schema_path
        )
        return a
transformer.register('XMLField', XMLFieldTransformation)

class CommaSeparatedIntegerFieldTransformation(CharFieldTransformation):
    def get_acceptable_types(self):
        return 'String of comma-separated integers'
transformer.register('CommaSeparatedIntegerField', CommaSeparatedIntegerFieldTransformation)

# Numeric fields
class NumericFieldTransformation(BaseFieldTransformation):
    def get_acceptable_types(self):
        return 'Number'
transformer.register('AutoField', NumericFieldTransformation)
transformer.register('SmallIntegerField', NumericFieldTransformation)
transformer.register('IntegerField', NumericFieldTransformation)
transformer.register('PositiveIntegerField', NumericFieldTransformation)
transformer.register('PositiveSmallIntegerField', NumericFieldTransformation)
transformer.register('FloatField', NumericFieldTransformation)

class DecimalFieldTransformation(NumericFieldTransformation):
    def get_attributes(self):
        a = super(DecimalFieldTransformation, self).get_attributes()
        a.update(
            maxDigits = self.field.max_digits,
            decimalPlaces = self.field.decimal_places,
        )
        return a
transformer.register('DecimalField', DecimalFieldTransformation)

# Temporal fields
class TemporalFieldTransformation(BaseFieldTransformation):
    def get_acceptable_types(self):
        return 'Date'

    def get_attributes(self):
        a = super(TemporalFieldTransformation, self).get_attributes()
        a.update(
            autoNow = self.field.auto_now,
            autoNowAdd = self.field.auto_now_add,
        )
        return a
transformer.register('DateField', TemporalFieldTransformation)
transformer.register('DateTimeField', TemporalFieldTransformation)
transformer.register('TimeField', TemporalFieldTransformation)

# Boolean fields
class BooleanFieldTransformation(BaseFieldTransformation):
    def get_acceptable_types(self):
        return 'Boolean'
transformer.register('NullBooleanField', BooleanFieldTransformation)
transformer.register('BooleanField', BooleanFieldTransformation)

# Relationship fields
class BaseRelationshipTransformation(BaseFieldTransformation):
    def get_related_obj(self):
        ops = self.field.rel.to._meta
        app_label, module_name = ops.app_label.capitalize(), ops.module_name.capitalize()
        return '.'.join([app_label, module_name])
        
    def get_js_type(self):
        return r"'" + self.get_related_obj() + r"'"

class ToOneFieldTransformation(BaseRelationshipTransformation):
    def get_acceptable_types(self):
        return self.get_related_obj()
    def get_record(self):
        return 'SC.Record.toOne'
transformer.register('OneToOneField', ToOneFieldTransformation)
transformer.register('ForeignKey', ToOneFieldTransformation)
transformer.register_reverse('OneToOneField', ToOneFieldTransformation)
    
class ToManyFieldTransformation(BaseRelationshipTransformation):
    def get_acceptable_types(self):
        return 'SC.RecordArray %s' % self.get_related_obj()
    def get_record(self):
        return 'SC.Record.toMany'
transformer.register('ManyToManyField', ToManyFieldTransformation)
transformer.register_reverse('ManyToManyField', ToManyFieldTransformation)
transformer.register_reverse('ForeignKey', ToManyFieldTransformation)


