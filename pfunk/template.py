from jinja2 import Template

graphql_template = Template("""
{% for e in enum_list %}
enum {{e.name}} {
    {% for p in e.choices %}
        {{p}}
    {% endfor %}
}
{% endfor %}
{% for t in collection_list %}
type {{t.get_class_name()|capitalize}} {
    {% for k,v in t._base_properties.items() %}
    {{k}}:{{v.get_graphql_type()}}
    {% endfor %}
}
{% endfor %}

type Query {
{% for t in collection_list %}
    {% if t._all_index %}
    all{{t._verbose_plural_name()|capitalize}}: [{{t.get_class_name()|capitalize}}] @index(name: "all_{{t._verbose_plural_name()}}")
    {% endif %}
{% endfor %}
}
""")