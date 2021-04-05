from jinja2 import Template

graphql_template = Template("""
{% for e in enum_list %}
enum e.name {
    {% for p in e %}
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
""")