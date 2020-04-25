from jinja2 import Template

type_template = Template("""
{% for e in graphql_enums %}
enum {{e.name}} {
    {% for c in e %}
    {{c}}
    {% endfor %}
}
{% endfor %}
{% for t in graphql_types %}
type {{t.name}} {
    {% for f in t.fields %}
    {{f.field_name}}:{{f.field_type}}
    {% endfor %}
}
{% endfor %}
""")