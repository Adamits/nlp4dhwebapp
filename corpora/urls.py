from django.conf.urls import url
from corpora import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'concordance', views.concordance, name='concordnace'),
    url(r'analysis', views.analysis, name='analysis'),
    url(r'annotate', views.annotate, name="annotate"),
    url(r'delete', views.delete, name="delete"),
]
