import json
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter()
def get_records(records, schema_name):
    return records[schema_name]

@register.filter()
def get_schema(schemas, schema_name):
    return schemas[schema_name]['Schema']