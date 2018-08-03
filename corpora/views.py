from django.shortcuts import render
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View

from .utils import *
from .forms import ConcordanceForm, AnalysisForm, GraphForm, CorpusForm
from .documents.corpus import Corpus
from .documents.graph import Graph
from .documents.counts_file import CountsFile
from .query import Query
from datetime import datetime

from django.http import JsonResponse
import pickle

def index(request):
    """
    Index page. Just lists the text document names (corpora, as we call them in the app)

    Also displays whether a corpus is annotated (i.e. indexed in elasticsearch) or not.
    """
    corpora_names = get_corpora_names()
    corpora = [Corpus(name) for name in corpora_names]

    paginator = Paginator(corpora, 50)
    page = request.GET.get('page')
    paginated_corpora = paginator.get_page(page)

    return render(request, 'index.html',
                  context={"corpora": paginated_corpora}
    )

def get_corpus(request, name):
    """
    The show page for a single corpus. Will only work if the corpus is in the es index
    i.e. is annotated.
    """
    corpus = Corpus.get_by_name(name)

    if corpus is not None:
        return render(request, 'corpus.html',
                        context={"corpus": corpus})
    else:
        return redirect('/corpora?')

def edit_corpus(request, name):
    """
    The edit page for a corpus. POST request to this method
    updates the corpus index with a new date.
    """
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
    """
    POST for corpora, to perform AllenNLP annotation from the NLP4DH
    script, that postprocesses in JSON to be indexed in ES.
    """
    names = request.POST.getlist('name')
    names = [name.rstrip('/') for name in names]
    a = Corpus.bulk_annotate(names)

    return redirect('/corpora?page=%s' % request.POST.get('page'))

def delete(request):
    """
    deletes the given corpora from the es index.

    does NOT delete the txt file in the shared data dir.
    """
    names = request.POST.getlist('name')
    names = [name.rstrip('/') for name in names]
    Corpus.bulk_delete(names)

    return redirect('/corpora?page=%s' % request.POST.get('page'))

def concordance(request, q=None):
    """
    Page for finding and highlighting concordance.
    """
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
    """
    Page for performing analysis to be displayed in a graph.
    """
    analysis = None
    graph_response = ""
    fig = None
    graph_form = GraphForm()

    if request.method == 'POST':
        query_dict = request.POST
        form = AnalysisForm(query_dict)
        if form.is_valid():
            analysis = Corpus.analyze(form.cleaned_data)
            graph = Graph.get_from_args(form.cleaned_data, analysis)

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

def download_counts(request):
    """
    Should be called by AJAX, this method
    makes the string of counts (or percentages, etc)
    that will be downloaded in a txt file.
    """
    analysis = None
    counts_file = CountsFile(args=None)
    if request.method == 'POST':
        query_dict = request.POST
        form = AnalysisForm(query_dict)
        if form.is_valid():
            counts_file = CountsFile(form.cleaned_data)
            counts_file.make_counts()

    return JsonResponse({"counts": counts_file.str})#", ".join([e for e in form.errors])})

def graph(request):
    """
    Should be called over AJAX.

    This method is for downloading the graph as a file in the given format
    """
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

