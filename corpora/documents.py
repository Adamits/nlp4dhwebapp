from elasticsearch_dsl import DocType, Search, Index, Text, Integer, Q
from elasticsearch import Elasticsearch, helpers

from django.conf import settings
import sys
import os
sys.path.append(settings.NLP4DH_DIR)
from lib.annotations import make_annotation_json

from .query import Query, Analyzer
from .subdocuments import *

# For graph
from django.http import HttpResponse
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
import base64
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

class Corpus():
    def __init__(self, name):
        self.name=name
        self.filename = settings.CORPORA_DIR + self.name

    def annotate(self):
        """
        Run the AllenNLP SRL;
        Parse the results and form a new JSON;
        Index that JSON with elasticsearch
        """
        annotation_json = make_annotation_json(self.filename)
        es = Elasticsearch([settings.ES_URL])
        return es.index(index='corpus', doc_type='corpus', body=annotation_json)

    def is_annotated(self):
        """
        Query the elasticsearch index for any Corpus
        with this name. If there is a match, return True.
        """
        es = Elasticsearch([settings.ES_URL])
        s = Search(using=es).query("match", name=self.name)
        for match in s:
            return True

        return False

    @classmethod
    def search_sentences(c, args, highlight_results=True):
        """
        Generates an ES query

        Return: a list of sentences that match the criteria
        """
        results = Query.generate(args)
        sentences = []
        highlights = []
        for corpus in results["hits"]["hits"]:
            # Get the inner hits dictionary, e.g. the sentence fields
            sentences += corpus["inner_hits"]["sentences"]["hits"]["hits"]

        # Return sentence objects, passing sentence args, and the next nested
        # layer of inner hits, e.g. potentially textSpans
        return [Sentence(s, args, highlight_results,\
                        s.get("highlight")) for s in sentences]

    @classmethod
    def search_text_spans(c, args):
        """
        Generates an ES query

        Return: a list of text_spans that match the criteria
        """
        results = Query.generate(args)
        text_spans = []
        # TextSpans are the innermost hits (2 nested levels deep)
        for corpus in results["hits"]["hits"]:
            # First nested field: sentence
            for sentence_args in corpus["inner_hits"]["sentences"]["hits"]["hits"]:
                if sentence_args.get("inner_hits"):
                    # Second nested field: text span
                    for text_spans_args in sentence_args["inner_hits"].values():
                        for text_span_args in text_spans_args["hits"]["hits"]:
                            text_spans.append(TextSpan(text_span_args["_source"]))

        return text_spans

    @classmethod
    def analyze(c, args):
        """
        Note this expects the query to be comma delimited
        So we split on comma and entertain multiple queries
        """
        queries = args.get("query").split(",")
        # Get a list of [{query: ..., etc}, {query: ..., etc}]
        # for all queries after splitting on ,
        tags_args = args.copy()
        tags_args.pop("query")
        args_list = [tags_args.copy() for q in queries]
        [a.update({"query": queries[i]})for i, a in enumerate(args_list)]
        # Just SRL right now, until we add more filters to form.
        query_tags = args.get("srl", [])
        if not query_tags:
            # If no tags in the query, just return the number of matches
            return_dict = {}
            for args in args_list:
                sentences = Corpus.search_sentences(args, highlight_results=False)
                count = " ".join([s.content for s in sentences]).count(args.get("query"))
                return_dict[args.get("query")] = count

            return return_dict

        return_dict = dict.fromkeys(queries, 0)
        for args in args_list:
            text_spans = Corpus.search_text_spans(args)

            for ts in text_spans:
                for tag, val in ts.get_tag_counts(query_tags).items():
                    return_dict[args.get("query")] += val

        return return_dict

class Graph():
    def __init__(self, x, labels, data):
        self.x = x
        self.labels = labels
        self.data = data
        self.figure = None
        self.figure = self.figure if self.figure else self._make_figure()

    def _make_figure(self):
        width = .1
        fig=plt.figure()
        ax=fig.add_subplot(111)

        ind = np.arange(len(self.x))

        for i, d in enumerate(self.data):
            ax.bar(ind + i*width, d, width, align='center')

        plt.legend([l for l in self.labels], loc='upper right')
        ax.set_xticks(ind + width/2)
        ax.set_xticklabels(self.x)

        return fig

    def get_base64(self):
        fig = self.figure
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)  # rewind to beginning of file
        fig_png = base64.b64encode(buf.getvalue())
        return fig_png.decode('utf8')

    def get_PDF(self, fn):
        pdf_path = settings.CORPORA_DIR + fn + '.pdf'
        f = self.figure
        canvas = FigureCanvas(f)
        print(f)
        f.savefig(pdf_path)

        return pdf_path

    def save_as(self, type):
        pass


def matches_query(text, query):
    """
    Need to check (again) if the tag content matches
    the original string query.

    As we expose more options to the user, this will need to be updated
    with those options. E.g. regex, case sensitive, etc.
    """
    return query.lower() in text.lower()
