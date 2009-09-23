{% autoescape off %}
//WARNING: THIS FILE IS GENERATED AUTOMATICALLY AND MAY BE OVERWRITTEN.
//IF YOU WISH TO MAKE CHANGES, SUBCLASS THE MODEL AND MAKE CHANGES THERE.

/** @private */
{{ app_label }}.Generated{{ model_name }} = SC.Record.extend(
/** {{ app_label }}.{{ model_name }}.prototype */ {
{% for field in generated_fields %}
/**
{{ field.comments }}
*/
{{ field.name }}: {{ field.record }}({{ field.js_type }}, {{ field.attributes }}),
{% endfor %}
primaryKey: 'pk'

});

SC.mixin({{ app_label }}.Generated{{ model_name }},
/** @scope {{ app_label }}.{{ model_name }} */ {
{% for option in meta %}
{{ option.name }}: {{ option.value }}{% if not forloop.last %},{% endif %}
{% endfor %}
});
{% endautoescape %}