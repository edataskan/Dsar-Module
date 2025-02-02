from django import template

register = template.Library()

@register.filter(name='add_attr')
def add_attr(value, arg):
    attrs = {}
    for pair in arg.split(','):
        key, val = pair.split('=')
        attrs[key.strip()] = val.strip()
    return value.as_widget(attrs=attrs)
