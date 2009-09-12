{% autoescape off %}
//WARNING: THIS FILE IS GENERATED AUTOMATICALLY AND MAY BE OVERWRITTEN.
//IF YOU WISH TO MAKE CHANGES, SUBCLASS THE MODEL AND MAKE CHANGES THERE.

{{ app_label }}._{{ module_name }} = SC.Record.extend(
/** {{ app_label }}._{{ module_name }}.prototype */ {

primaryKey: 'pk',

{{ generated_fields }}

});

{{ app_label }}._{{ module_name }}.djangoModel = '{{ app_label|lower }}.{{ module_name|lower }}';
{% endautoescape %}