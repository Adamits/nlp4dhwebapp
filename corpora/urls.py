from django.conf.urls import url
from django.urls import path
from corpora import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'concordance', views.concordance, name='concordnace'),
    url(r'analysis', views.analysis, name='analysis'),
    url(r'graph', views.graph, name='graph'),
    url(r'annotate', views.annotate, name="annotate"),
    url(r'delete', views.delete, name="delete"),
    path('/<str:name>', views.get_corpus),
    path('/<str:name>/edit', views.edit_corpus, name='edit_corpus'),
]
