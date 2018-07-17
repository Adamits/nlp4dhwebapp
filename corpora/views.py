from django.shortcuts import render
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse
from .utils import *
from .forms import ConcordanceForm, AnalysisForm
from .documents import Corpus, Graph

import json

def index(request):
    corpora_names = get_corpora_names()
    corpora = [Corpus(name) for name in corpora_names]

    paginator = Paginator(corpora, 20)
    page = request.GET.get('page')
    paginated_corpora = paginator.get_page(page)
    return render(request, 'index.html',
                  context={"corpora": paginated_corpora}
    )

def concordance(request, q=None):
    sentences = None
    num_sentences = None

    if request.method == 'POST':
        query_dict = request.POST
        form = ConcordanceForm(query_dict)

        if form.is_valid():
            sentences = Corpus.search_sentences(form.cleaned_data)
            num_sentences = len(sentences)

    else:
        form = ConcordanceForm(initial={'max_examples': 100})

    return render(request, 'concordance.html',
                  context={"form": form,
                            "sentences": sentences,
                            "num_sentences": num_sentences})

def analysis(request):
    analysis = None
    chart_type = None
    chart_dict = {}

    if request.method == 'POST':
        query_dict = request.POST
        form = AnalysisForm(query_dict)

        if form.is_valid():
            analysis = Corpus.analyze(form.cleaned_data)
            print(analysis)
            chart_type = form.cleaned_data.get("chart_type", "bar")
            chart_labels = ["LABEL"]
            tags = list(analysis.keys())
            chart_datasets = [ \
                                            {"label": t,
                                             "data": [analysis.get(t)],
                                             "backgroundColor": get_color(t)
                                            } \
                                        for t in tags]
            chart_dict = {"labels": chart_labels, "datasets": chart_datasets}

    else:
        form = AnalysisForm()

    return render(request, 'analysis.html',
                    context={
                                "form": form,
                                "analysis": analysis,
                                "chart_type": chart_type,
                                "chart_data": json.dumps(chart_dict)
                            }
            )
def get_graph(request):
    graph = Graph()

def save_graph(request):
    pass

def annotate(request):
    name = request.POST.get('name')
    name = name.rstrip('/')
    corpus = Corpus(name)
    a = corpus.annotate()
    return redirect('/corpora?page=%s' % request.POST.get('page'))

def delete(request):
    print(request.POST.get('name'))
    return redirect('/corpora?page=%s' % request.POST.get('page'))

