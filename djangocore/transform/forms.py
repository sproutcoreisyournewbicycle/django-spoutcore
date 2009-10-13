# Django dependencies.
from django.db.models.fields import NOT_PROVIDED

# Intra-app dependencies.
from djangocore.utils import camelize, lcamelize, splitwords

class AlreadyRegistered(Exception):
    """Raised when trying to register a content type that has already
    been registered."""
    pass

class NotRegistered(Exception):
    """Raised when trying to unregister a content type that isn't
    registered."""
    pass

class WidgetTransformer(object):
    """Used to translate/transform django form widgets to SC views"""
    def __init__(self, widget, extra_attributes, ignore=None):
        self.widget = widget
        self.extra_attributes = extra_attributes
        self.ignore = ignore

    def get_widget_attrs_for(self, li):
        """Helper function to get the specified widget attributes."""        
        attributes_dict = {}

        # Loop over the list to find corresponding Python and SproutCore
        # attribute names.
        for l in li:
            if not hasattr(l, '__iter__'):
                l = [l]
                
            if len(l) == 1:
                pyname, scname = l[0], lcamelize(l[0])
                ignore = self.ignore
            elif len(l) == 2:
                pyname, scname = l[0], l[1]
                ignore = self.ignore
            elif len(l) == 3:
                pyname, scname, ignore = l[0], l[1], l[2]
        
            # Get the attribute's value, ignoring it if it doesn't exist or is
            # equal to the provided ignore value.
            try:
                attr = getattr(self.widget, pyname)
                if callable(attr):
                    attr = attr()
                if attr != ignore:
                    attributes_dict[scname] = attr

            # TODO: how do we want to log this problem, since it occurs at
            # runtime, instead of beforehand. Possibly with smart defaults?
            except AttributeError:
                print "%s has no attribute named '%s'" % (self.widget, pyname)
            except TypeError, e:
                print "Unabled to call method '%s' on %s: %s" % \
                  (pyname, self.widget, e)
            except:
                print "An error occurred while attempting to get the value " \
                 "for '%s' on %s" % (pyname, self.widget)
            
        attributes_dict.update(
            # Add in the name of the actual field class
            widgetClass = self.widget.__class__.__name__,
        )

        return attributes_dict

    def render(self):
        attributes = [
            # python attr name      # sproutcore name
            ('attrs',               'attributes'),
        ]

        attributes.extend(self.extra_attributes)
        attributes_dict = self.get_widget_attrs_for(attributes)
        return attributes_dict
    
class FieldTransformer(object):
    """ Transforms the attrs of an SC.FieldView (All of the fields that would normaly be in a form subclass SC.FieldView) """
    def __init__(self, field, extra_attributes, ignore=None):
        self.field = field
        self.extra_attributes = extra_attributes
        self.ignore = ignore
    
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
                ignore = self.ignore
            elif len(l) == 2:
                pyname, scname = l[0], l[1]
                ignore = self.ignore
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

            # TODO: how do we want to log this problem, since it occurs at
            # runtime, instead of beforehand. Possibly with smart defaults?
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
            
    def render(self):
        attributes = [
            # python attr name      # sproutcore name
            ('label',               'title'),
            ('required',            'isRequired'),
#            ('error_messages',      'errorMessages'),
            
            # python attr name      # sproutcore name   # ignore
            ('initial',             'defaultValue',     None),
            ('help_text',           'hint',             ""),
        ]

        attributes.extend(self.extra_attributes)
        attributes_dict = self.get_field_attrs_for(attributes)
        return attributes_dict

class ModelChoiceFieldTransformer(FieldTransformer):
    def render(self):
        attributes_dict = super(ModelChoiceFieldTransformer, self).render()
        ops = self.field.queryset.model._meta
        attributes_dict.update(
            # Choices is an iterator, so we have to force it into a list
            choices = list(self.field.choices),
            emptyLabel = self.field.empty_label,
            modelClass = '.'.join([ops.app_label, ops.module_name])
        )
        return attributes_dict

class FormTransformer(object):
    def __init__(self):
        self._field_transformers = {}
        self._widget_transformers = {}
    
    def register_widget(self, name, transformer=WidgetTransformer, extra_attributes=None):
        if name in self._widget_transformers:
            raise AlreadyRegistered("A transformer for %s is already registered" % name)
        if not extra_attributes:
            extra_attributes = []
        elif not hasattr(extra_attributes, '__iter__'):
            extra_attributes = [extra_attributes]
        self._widget_transformers[name] = transformer, extra_attributes
    
    def unregister_widget(self, name):
        if ctype not in self._widget_transformers:
            raise NotRegistered("No transformer for %s is registered" % name)
        del self._widget_transformers[name]
        
    def register_field(self, name, transformer=FieldTransformer, extra_attributes=None):
        if name in self._field_transformers:
            raise AlreadyRegistered("A transformation for %s is already registered" % name)
        if not extra_attributes:
            extra_attributes = []
        elif not hasattr(extra_attributes, '__iter__'):
            extra_attributes = [extra_attributes]
        self._field_transformers[name] = transformer, extra_attributes

    def unregister_field(self, name):
        if ctype not in self._field_transformers:
            raise NotRegistered("No transformer for %s is registered" % name)
        del self._field_transformers[name]

    def get_field_transformer(self, name):
        if not isinstance(name, basestring):
            name = name.__class__.__name__
        return self._field_transformers.get(name)

    def get_widget_transformer(self, name):
        if not isinstance(name, basestring):
            name = name.__class__.__name__
        return self._widget_transformers.get(name)
    
    def generate_fields(self, form):
        field_list = []
        for i, name in enumerate(form.base_fields.keyOrder):
            
            # Transform the field.
            field = form.base_fields.get(name)
            FieldTransformer, extra_attributes = self.get_field_transformer(field)
            field_dict = FieldTransformer(field, extra_attributes).render()
            
            if 'title' not in field_dict or not field_dict['title']:
                field_dict['title'] = splitwords(name).title()
            
            # Transform the field's widget.
            widget = field.widget
            WidgetTransformer, extra_attributes = self.get_widget_transformer(widget)
            widget_dict = WidgetTransformer(widget, extra_attributes).render()
            
            field_dict.update(
                key = name,
                fieldOrder = i,
                widget = widget_dict,
            )
            
            field_list.append(field_dict)

        return field_list
        
    def render(self, form):
        form_dict = {
            'formName': form.__name__,
            'submitionURL': None, # TODO: fix
            'method': None, # TODO: fix
            'fields': self.generate_fields(form),
        }
        
        return form_dict
        
#        from djangocore.utils import camelize, lcamelize, deconstruct
#        from django.utils import simplejson
#        from django.core.serializers.json import DjangoJSONEncoder
#        
#        return simplejson.dumps(deconstruct(form_dict), cls=JSONEncoder, indent=4, ensure_ascii=False)


transformer = FormTransformer()

# Widgets
transformer.register_widget('TextInput')
transformer.register_widget('PasswordInput', extra_attributes='render_value')
transformer.register_widget('HiddenInput')
transformer.register_widget('MultipleHiddenInput')
transformer.register_widget('FileInput')
transformer.register_widget('DateInput', extra_attributes='format')
transformer.register_widget('DateTimeInput', extra_attributes='format')
transformer.register_widget('TimeInput', extra_attributes='format')
transformer.register_widget('Textarea')
transformer.register_widget('CheckboxInput')
transformer.register_widget('Select')
transformer.register_widget('NullBooleanSelect')
transformer.register_widget('SelectMultiple')
transformer.register_widget('RadioSelect')
transformer.register_widget('CheckboxSelectMultiple')
transformer.register_widget('MultiWidget')
transformer.register_widget('SplitDateTimeWidget', extra_attributes=('date_format', 'time_format'))
transformer.register_widget('SelectDateWidget')

#Fields
transformer.register_field('BooleanField')
transformer.register_field('CharField', extra_attributes=('max_length', 'min_length'))
transformer.register_field('ChoiceField', extra_attributes='choices')
transformer.register_field('TypeChoiceField', extra_attributes=('choices', 'empty_value'))
transformer.register_field('DateField', extra_attributes='input_formats')
transformer.register_field('DateTimeField', extra_attributes='input_formats')
transformer.register_field('DecimalField', extra_attributes=('max_value', 'min_value', 'max_digits', 'decimal_places'))
transformer.register_field('EmailField', extra_attributes=('max_length', 'min_length'))
transformer.register_field('FileField')
transformer.register_field('FilePathField', extra_attributes=('path', 'recursive', 'match'))
transformer.register_field('FloatField')
transformer.register_field('ImageField')
transformer.register_field('IntegerField', extra_attributes=('max_value', 'min_value'))
transformer.register_field('IPAddressField')
transformer.register_field('MultipleChoiceField', extra_attributes='choices')
transformer.register_field('NullBooleanField')
transformer.register_field('RegexField', extra_attributes='regex')
transformer.register_field('TimeField', extra_attributes='input_formats')
transformer.register_field('URLField', extra_attributes=('max_length', 'min_length', 'verify_exists', 'validator_user_agent'))
transformer.register_field('SplitDateTimeField', extra_attributes=('input_date_formats', 'input_time_formats'))
transformer.register_field('ComboField') # Not documented
transformer.register_field('MultiValueField') # Not documented
transformer.register_field('ModelChoiceField', transformer=ModelChoiceFieldTransformer)
transformer.register_field('ModelMultipleChoiceField', transformer=ModelChoiceFieldTransformer)














sample = """
{
    "submitionURL": null, 
    "method": null, 
    "fields": [
        {
            "widget": {
                "attributes": {}, 
                "widgetClass": "HiddenInput"
            }, 
            "key": "security_hash", 
            "fieldOrder": 0, 
            "title": "Security Hash", 
            "minLength": 40, 
            "isRequired": true, 
            "fieldClass": "CharField", 
            "maxLength": 40
        }, 
        {
            "isRequired": true, 
            "widget": {
                "attributes": {}, 
                "widgetClass": "HiddenInput"
            }, 
            "key": "content_type", 
            "fieldClass": "CharField", 
            "title": "Content Type", 
            "fieldOrder": 1
        }, 
        {
            "isRequired": true, 
            "widget": {
                "attributes": {}, 
                "widgetClass": "HiddenInput"
            }, 
            "key": "object_pk", 
            "fieldClass": "CharField", 
            "title": "Object Pk", 
            "fieldOrder": 2
        }, 
        {
            "isRequired": true, 
            "widget": {
                "attributes": {}, 
                "widgetClass": "HiddenInput"
            }, 
            "key": "ip_address", 
            "fieldClass": "CharField", 
            "title": "Ip Address", 
            "fieldOrder": 3
        }, 
        {
            "isRequired": true, 
            "widget": {
                "attributes": {}, 
                "widgetClass": "HiddenInput"
            }, 
            "key": "timestamp", 
            "fieldClass": "IntegerField", 
            "title": "Timestamp", 
            "fieldOrder": 4
        }, 
        {
            "isRequired": false, 
            "widget": {
                "attributes": {}, 
                "widgetClass": "TextInput"
            }, 
            "key": "honeypot", 
            "fieldClass": "CharField", 
            "title": "If you enter anything in this field your comment will be treated as spam", 
            "fieldOrder": 5
        }, 
        {
            "isRequired": true, 
            "widget": {
                "attributes": {
                    "rows": "10", 
                    "cols": "40"
                }, 
                "widgetClass": "Textarea"
            }, 
            "key": "comment", 
            "fieldClass": "CharField", 
            "maxLength": 3000, 
            "fieldOrder": 6, 
            "title": "Comment"
        }
    ], 
    "formName": "UserCommentForm"
}
"""