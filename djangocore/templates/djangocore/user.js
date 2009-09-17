{% autoescape off %}
sc_require('{{ generated_file_name }}');

{{ app_label }}.{{ model_name }} = {{ app_label }}._{{ model_name }}.extend(
/** {{ app_label }}.{{ model_name }}.prototype */ {

  // Add SproutCore specific code here

});
{% endautoescape %}