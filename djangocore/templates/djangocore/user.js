{% autoescape off %}
sc_require('{{ generated_file_name }}');

{{ app_label }}.{{ module_name }} = {{ app_label }}._{{ module_name }}.extend(
/** {{ app_label }}.{{ module_name }}.prototype */ {

  // Add SproutCore specific code here

});
{% endautoescape %}