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
    {% if t.all_index %}
    all{{t.get_verbose_plural_name()|capitalize}}: [{{t.get_class_name()|capitalize}}] @index(name: "all_{{t.get_verbose_plural_name()}}")
    {% endif %}
{% endfor %}
}

{{extra_graphql}}
""")

wsgi_template = Template("""
from envs import env
from valley.utils import import_util

project = import_util(env('PFUNK_PROJECT', '{{PFUNK_PROJECT}}'))
app = project.wsgi_app

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    run_simple('127.0.0.1', 3434, app, use_debugger=True, use_reloader=True)
""")

project_template = Template("""
from pfunk import Project


project = Project()
handler = project.event_handler
""")

collections_templates = Template("""
from pfunk import Collection

# Write some collections here
""")

key_template = Template("""
KEYS = {{keys}}
""")