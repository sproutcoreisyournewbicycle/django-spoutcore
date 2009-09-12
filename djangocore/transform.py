# Django dependencies.
from django.db.models import *
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

class BaseFieldTransform(object):
    def __init__(self, field, model):
        super(BaseFieldTransform, self).__init__()
        self.field = field
        self.model = model
        
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
            defaultValue = self.field.default,
            isEditable = self.field.editable,
            isUnique = self.field.unique,
            djangoField = self.field.__class__.__name__,
        ))
        
        # We only add these to the attributes if they are actually defined.
        uniques = dict(
            isUniqueForDate = self.field.unique_for_date,
            isUniqueForMonth = self.field.unique_for_month,
            isUniqueForYear = self.field.unique_for_year,
        )
        
        # Cycle through and add the ones with values.
        for key, value in uniques.items():
            if value != None:
                a[key] = value

        return a
        
    def get_comments(self):
        c = Comments(['@type %s' % self.get_acceptable_types()])
        if self.field.help_text:
            c.insert(0, smart_str(self.field.help_text))
        return c
    
    def should_render(self):
        return True
    
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
class BaseStringTransform(BaseFieldTransform):
    def get_acceptable_types(self):
        return 'String'
        
class TextFieldTransform(BaseStringTransform):
    pass
    
class CharFieldTransform(BaseStringTransform):
    def get_attributes(self):
        a = super(CharFieldTransform, self).get_attributes()
        a.update(
            maxLength = self.field.max_length
        )
        return a

class SlugFieldTransform(CharFieldTransform):
    pass    

class EmailFieldTransform(CharFieldTransform):
    pass    

class FileFieldTransform(CharFieldTransform):
    def get_attributes(self):
        a = super(FileFieldTransform, self).get_attributes()
        a.update(
            uploadTo = self.field.upload_to
        )
        return a

class ImageFieldTransform(FileFieldTransform):
    def get_attributes(self):
        a = super(ImageFieldTransform, self).get_attributes()
        a.update(
            heightField = self.field.height_field,
            widthField = self.field.width_field
        )
        return a

class FilePathFieldTransform(CharFieldTransform):
    def get_attributes(self):
        a = super(FilePathFieldTransform, self).get_attributes()
        a.update(
            path = self.field.path,
            match = self.field.match,
            recursive = self.field.recursive,
        )
        return a

class URLFieldTransform(CharFieldTransform):
    def get_attributes(self):
        a = super(URLFieldTransform, self).get_attributes()
        a.update(
            verifyExists = self.field.verify_exists
        )
        return a

class XMLFieldTransform(CharFieldTransform):
    def get_attributes(self):
        a = super(XMLFieldTransform, self).get_attributes()
        a.update(
            schemaPath = self.field.schema_path
        )
        return a

class IPAddressFieldTransform(CharFieldTransform):
    pass    

class CommaSeparatedIntegerFieldTransform(CharFieldTransform):
    def get_acceptable_types(self):
        return 'Comma separated string of integers'

# Numeric fields
class BaseNumericTransform(BaseFieldTransform):
    def get_acceptable_types(self):
        return 'Number'
    
class IntegerFieldTransform(BaseNumericTransform):
    pass

class SmallIntegerFieldTransform(BaseNumericTransform):
    pass

class PositiveIntegerFieldTransform(BaseNumericTransform):
    pass

class PositiveSmallIntegerFieldTransform(BaseNumericTransform):
    pass
    
class FloatFieldTransform(BaseNumericTransform):
    pass

class DecimalFieldTransform(BaseNumericTransform):
    def get_attributes(self):
        a = super(DecimalFieldTransform, self).get_attributes()
        a.update(
            maxDigits = self.field.max_digits,
            decimalPlaces = self.field.decimal_places,
        )
        return a

class AutoFieldTransform(IntegerFieldTransform):
    def should_render(self):
        return False

# Temporal fields
class BaseTemporalTransform(BaseFieldTransform):
    def get_acceptable_types(self):
        return 'Date'

    def get_attributes(self):
        a = super(BaseTemporalTransform, self).get_attributes()
        a.update(
            autoNow = self.field.auto_now,
            autoNowAdd = self.field.auto_now_add,
        )
        return a

class DateFieldTransform(BaseTemporalTransform):
    pass

class TimeFieldTransform(BaseTemporalTransform):
    pass

class DateTimeFieldTransform(BaseTemporalTransform):
    pass

# Boolean fields
class BaseBooleanTransform(BaseFieldTransform):
    def get_acceptable_types(self):
        return 'Boolean'

class BooleanFieldTransform(BaseBooleanTransform):
    pass

class NullBooleanFieldTransform(BaseBooleanTransform):
    pass

# Relationship fields
class BaseRelationshipTransform(BaseFieldTransform):
    def get_related_obj(self):
        ops = self.field.rel.to._meta
        app_label, module_name = ops.app_label.capitalize(), ops.module_name.capitalize()
        return '.'.join([app_label, module_name])
        
    def get_js_type(self):
        return r"'" + self.get_related_obj() + r"'"

class ToOneFieldTransform(BaseRelationshipTransform):
    def get_acceptable_types(self):
        return self.get_related_obj()
    
    def get_record(self):
        return 'SC.Record.toOne'
    
class ToManyFieldTransform(BaseRelationshipTransform):
    def get_acceptable_types(self):
        return 'SC.RecordArray %s' % self.get_related_obj()

    def get_record(self):
        return 'SC.Record.toMany'

FIELD_TRANSFORMS = {
    AutoField: AutoFieldTransform,
    BooleanField: BooleanFieldTransform,
    CharField: CharFieldTransform,
    CommaSeparatedIntegerField: CommaSeparatedIntegerFieldTransform,
    DateField: DateFieldTransform,
    DateTimeField: DateTimeFieldTransform,
    DecimalField: DecimalFieldTransform,
    EmailField: EmailFieldTransform,
    FileField: FileFieldTransform,
    FilePathField: FilePathFieldTransform,
    FloatField: FloatFieldTransform,
    ImageField: ImageFieldTransform,
    IntegerField: IntegerFieldTransform,
    IPAddressField: IPAddressFieldTransform,
    NullBooleanField: NullBooleanFieldTransform,
    PositiveIntegerField: PositiveIntegerFieldTransform,
    PositiveSmallIntegerField: PositiveSmallIntegerFieldTransform,
    SlugField: SlugFieldTransform,
    SmallIntegerField: SmallIntegerFieldTransform,
    TextField: TextFieldTransform,
    TimeField: TimeFieldTransform,
    URLField: URLFieldTransform,
    XMLField: XMLFieldTransform,

    # Related fields
    OneToOneField: ToOneFieldTransform,
    ForeignKey: ToOneFieldTransform,
}

REVERSE_TRANSFORMS = {
    OneToOneField: ToOneFieldTransform,
    ForeignKey: ToManyFieldTransform,
}

class ModelTransform(object):
    def __init__(self, model):
        super(ModelTransform, self).__init__()
        self.model = model
    
    def render(self):
        fields = []
        ops = self.model._meta
        # Regular fields and one-to-xxx relationships
        for field in ops.fields:
            try:
                f = FIELD_TRANSFORMS[field.__class__](field, self.model).render()
                if f: fields.append(f)
            except KeyError:
                # Got a custom field type, so we punt on it.
                pass
                
        # Many-to-many relationships
        m2m_fields = ops.many_to_many # forward m2m
        m2m_fields = [obj.field for obj in ops.get_all_related_many_to_many_objects()] # backward m2m
        for field in m2m_fields:
            f = ToManyFieldTransform(field, self.model).render()
            if f: fields.append(f)

        # Reverse one-to-xxx relationships
        reverse_fields = [obj.field for obj in ops.get_all_related_objects()] 
        for field in reverse_fields:
            f = REVERSE_TRANSFORMS[field.__class__](field, self.model).render()
            if f: fields.append(f)
         
        return ',\n\n'.join(fields)
    
    def __str__(self):
        return self.render()

 
