# app_estoque/templatetags/json_filters.py

import json
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.template import Library

register = Library()

@register.filter
def jsonify(object):
    if isinstance(object, QuerySet):
        return serialize('json', object)
    return json.dumps(object)