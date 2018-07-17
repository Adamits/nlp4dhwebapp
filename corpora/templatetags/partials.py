from django import template

register = template.Library()

@register.inclusion_tag('_corpora_viewer.html')
def show_corpora(corpora):
    return {'corpora': corpora}

@register.inclusion_tag('_navbar.html')
def show_nav(active):
    return {'active': active}

