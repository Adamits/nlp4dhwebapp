from django import template

register = template.Library()

@register.inclusion_tag('_corpora_viewer.html')
def show_corpora(corpora):
    return {'corpora': corpora}

@register.inclusion_tag('_navbar.html')
def show_nav(active):
    return {'active': active}

@register.inclusion_tag('_graph.html')
def show_graph(chart_type, chart_data):
    return {'chart_type': chart_type, 'chart_data': chart_data}

