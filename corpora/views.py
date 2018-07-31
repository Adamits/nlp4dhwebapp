from django.shortcuts import render
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View

from .utils import *
from .forms import ConcordanceForm, AnalysisForm, GraphForm, CorpusForm
from .documents import Corpus, Graph
from .query import Query
from datetime import datetime

from django.http import JsonResponse
import pickle

def index(request):
    corpora_names = get_corpora_names()
    corpora = [Corpus(name) for name in corpora_names]

    paginator = Paginator(corpora, 20)
    page = request.GET.get('page')
    paginated_corpora = paginator.get_page(page)

    return render(request, 'index.html',
                  context={"corpora": paginated_corpora}
    )

def get_corpus(request, name):
    corpus = Corpus.get_by_name(name)

    if corpus is not None:
        return render(request, 'corpus.html',
                        context={"corpus": corpus})
    else:
        return redirect('/corpora?')

def edit_corpus(request, name):
    corpus = Corpus.get_by_name(name)
    form = CorpusForm()

    if request.method == 'POST':
        #Just for updating the date.
        year = request.POST.get('year')
        if corpus is not None:
            corpus.update_year(year)

        return redirect('/corpora/%s' % name)
    else:
        form = CorpusForm(initial={'year': corpus.get_year()})

        return render(request, 'edit_corpus.html',
                        context={"corpus": corpus,
                                 "form": form})

def annotate(request):
    name = request.POST.get('name')
    name = name.rstrip('/')
    corpus = Corpus(name)
    a = corpus.annotate()

    return redirect('/corpora?page=%s' % request.POST.get('page'))

def delete(request):
    idx = request.POST.get('id')
    corpus = Corpus.get_by_id(idx)
    if corpus:
        x=corpus.delete()

    return redirect('/corpora?page=%s' % request.POST.get('page'))

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
    graph_response = ""
    fig = None
    graph_form = GraphForm()

    if request.method == 'POST':
        query_dict = request.POST
        form = AnalysisForm(query_dict)

        if form.is_valid():
            graph_type = form.cleaned_data.get("chart_type", "bar")
            graph_years = form.cleaned_data.get("years", [None])
            graph_years= [y.strip() for y in graph_years.split(",")]

            analysis = Corpus.analyze(form.cleaned_data)
            graph_labels = list(analysis.keys())
            if Query.is_aggregation_query(form.cleaned_data):
                # Data should be [#keywords x #years]
                graph_data = [list(y.values()) for y in analysis.values()]
            else:
                # Even if no years, data should be a list of lists
                graph_data = [[v] for v in analysis.values()]

            graph = Graph(graph_years, graph_labels, graph_data)

            graph_response = graph.get_base64()
            request.session['graph'] = pickle.dumps(graph)

    else:
        form = AnalysisForm()

    return render(request, 'analysis.html',
                context={
                            "form": form,
                            "graph_form": graph_form,
                            "analysis": analysis,
                            "figure": graph_response
                        })

def graph(request):
    if request.method == 'POST':
        args_dict = request.POST
        form = GraphForm(args_dict)
        if form.is_valid():
            data = form.cleaned_data
            graph_name = data.get("name")
            graph_type = data.get("file_type")
            # There will be a Graph object in the session
            # If there was a query
            graph = request.session.get('graph', None)
            if graph is not None:
                graph = pickle.loads(graph)
                pdf_path = graph.save_as(graph_name, graph_type)

                return JsonResponse({"message": "Successfully saved to %s" % pdf_path})

    return JsonResponse({"message": ", ".join([e for e in form.errors])})

