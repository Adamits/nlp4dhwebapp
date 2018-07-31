from elasticsearch_dsl import DocType, Search, Index, Text, Integer, Q
from elasticsearch import Elasticsearch, helpers
from elasticsearch_dsl.connections import connections

from django.conf import settings
import sys
import os
sys.path.append(settings.NLP4DH_DIR)
from lib.annotations import make_annotation_json

from .query import Query, Analyzer
from .subdocuments import *

# For graph
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
import base64
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

connections.create_connection(hosts=[settings.ES_URL])
es = Elasticsearch([settings.ES_URL])

class Corpus():
    def __init__(self, name, cid=None, year=None):
        self.name = name
        self.id = cid
        self.year = year
        self.filename = settings.CORPORA_DIR + self.name

    def get_id(self):
        if self.id:
            return self.id
        else:
            s = Search().query("match", name=self.name)
            for hit in s:
                return hit.meta.id

    def is_annotated(self):
        """
        Query the elasticsearch index for any Corpus
        with this name. If there is a match, return True.
        """
        s = Search().query("match", name=self.name)
        for match in s:
            return True

        return False

    def get_year(self):
        """
        Check for year attribute instantiated already

        If none, set that attribute so next lookup on this instance
        does not require querying ES.
        """
        if self.year:
            return self.year
        else:
            s = Search().query("match", name=self.name)
            for hit in s:
                self.year = hit.year
                return hit.year

    def get_text(self):
        s = Search().query("match", name=self.name)
        for hit in s:
            return ' '.join([s.content for s in hit.sentences])

    def annotate(self):
        """
        Run the AllenNLP SRL;
        Parse the results and form a new JSON;
        Index that JSON with elasticsearch
        """
        annotation_json = make_annotation_json(self.filename)
        x=es.index(index='corpus', doc_type='corpus', body=annotation_json)
        self._es_update_callback()

        return x

    def update_year(self, year):
        """
        This is for updating the year on the
        actual ES record.
        """
        self.year = year
        x = es.update(index='corpus', doc_type="corpus", id=self.id,
                     body={
                        "doc": {
                            "year": year
                        }
                     }
                )
        self._es_update_callback()

        return x

    def delete(self):
        """
        Find the indexed es document corresponding to this instance
        and delete it.
        """
        x=es.delete(index='corpus', doc_type="corpus", id=self.id)
        self._es_update_callback()

        return x

    @classmethod
    def get_by_id(c, cid):
        """
        Return a corpus object with the given ID in ElasticSearch
        """
        if cid:
            record = es.get(index="corpus", doc_type="corpus", id=cid)

            year = record["_source"]["year"]
            name = record["_source"]["name"]
            return Corpus(name, cid=cid, year=year)

    @classmethod
    def get_by_name(c, name):
        """
        Return a corpus object with the given name in ElasticSearch
        """
        s = Search().query("match", name=name)
        for hit in s:
            year = hit.year
            cid = hit.meta.id
            name = hit.name
            return Corpus(name, cid=cid, year=year)

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
        text_spans = []
        results = Query.generate(args)

        for corpus in results["hits"]["hits"]:
            text_spans += Corpus._get_text_spans_from_corpus_doc(corpus)

        return text_spans

    @classmethod
    def aggregate_text_spans(c, args):
        """
        Generates an ES query

        Return: a dict of {agg_term: list of text_spans}

        **Note that right now aggragations (e.g. agg_term) are ONLY by year
        """
        results = Query.generate_aggregate_query(args)
        # Only aggregating by years...
        years = [y.strip() for y in args.get("years").split(",")]
        aggs_dict = {y: [] for y in years}
        for agg in results:
            text_spans = []
            nested_agg = agg.get("all")

            for corpus in nested_agg["hits"]["hits"]:
                if agg.get("key") in aggs_dict.keys():
                    # Check that this aggregation's year is
                    # in the years that we are interested in.
                    aggs_dict[agg.get("key")] += \
                                Corpus._get_text_spans_from_corpus_doc(corpus)

        return aggs_dict

    @classmethod
    def aggregate_sentences(c, args):
        """
        Generates an ES query

        Return: a dict of {agg_term: list of sentences}

        **Note that right now aggragations (e.g. agg_term) are ONLY by year
        """
        results = Query.generate_aggregate_query(args)
        # Only aggregating by years...
        years = [y.strip() for y in args.get("years").split(",")]
        aggs_dict = {y: [] for y in years}
        for agg in results:
            nested_agg = agg.get("all")

            for corpus in nested_agg["hits"]["hits"]:
                if agg.get("key") in aggs_dict.keys():
                    aggs_dict[agg.get("key")] += \
                                Corpus._get_sentences_from_corpus_doc(corpus, args)

        return aggs_dict

    @classmethod
    def analyze(c, args):
        """
        Note this expects the query to be comma delimited
        So we split on comma and entertain multiple queries, same with
        the dates
        """
        is_aggregation = Query.is_aggregation_query(args)
        # Get a list of [{query: ..., etc}, {query: ..., etc}]
        # for all queries after splitting on ,
        queries, args_list = Corpus._split_args(args)
        # Just SRL right now, until we add more filters to form.
        query_tags = args.get("srl", [])
        return_dict = dict.fromkeys(queries, 0)
        # Purely a content query, we only care about sentence level
        if not query_tags:
            for args in args_list:
                if is_aggregation:
                    sentences_dict = Corpus.aggregate_sentences(args)
                    count_dict = dict.fromkeys(sentences_dict.keys(), 0)
                    for k, sentences in sentences_dict.items():
                        # TODO this needs to count per ES term counts,
                        # otherwise it only looks for string literal
                        # For now use lower b/c that seems to be what ES does..
                        # Long term solution is probably to let a user define the regex themselves
                        # and then use that in both ES query, and count.
                        count = " ".join([s.content.lower() for s in sentences]).count(args.get("query").lower())
                        count_dict[k] = count

                    return_dict[args.get("query")] = count_dict
                else:
                    sentences = Corpus.search_sentences(args, highlight_results=False)
                    # TODO this needs to count per ES term counts,
                        # otherwise it only looks for string literal
                        # For now use lower b/c that seems to be what ES does..
                        # Long term solution is probably to let a user define the regex themselves
                        # and then use that in both ES query, and count.
                    return_dict[args.get("query")] += \
                                " ".join([s.content.lower() for s in sentences]).count(args.get("query").lower())

            return return_dict

        # Otherwise our query has some tags, so we look at the textSpan level
        for args in args_list:
            if is_aggregation:
                text_spans_dict = Corpus.aggregate_text_spans(args)
                count_dict = dict.fromkeys(text_spans_dict.keys(), 0)
                for k, text_spans in text_spans_dict.items():
                    for ts in text_spans:
                        for tag, val in ts.get_tag_counts(query_tags).items():
                            count_dict[k] += val

                return_dict[args.get("query")] = count_dict
            else:
                text_spans = Corpus.search_text_spans(args)
                for ts in text_spans:
                    for tag, val in ts.get_tag_counts(query_tags).items():
                        return_dict[args.get("query")] += val

        return return_dict

    @classmethod
    def _get_text_spans_from_corpus_doc(c, corpus):
        """
        Given the es response at the corpus level,
        get text span objects from it and return in a list
        """
        text_spans = []
        # First nested field: sentence
        for sentence_args in corpus["inner_hits"]["sentences"]["hits"]["hits"]:
            if sentence_args.get("inner_hits"):
                # Second nested field: text span
                for text_spans_args in sentence_args["inner_hits"].values():
                    for text_span_args in text_spans_args["hits"]["hits"]:
                        text_spans.append(TextSpan(text_span_args["_source"]))

        return text_spans

    @classmethod
    def _get_sentences_from_corpus_doc(c, corpus, args):
        """
        Given the es response at the corpus level,
        get sentence objects from it and return in a list
        """
        sentences = []
        # First nested field: sentence
        for s in corpus["inner_hits"]["sentences"]["hits"]["hits"]:
            sentences.append(Sentence(s, args, highlight_results=False))

        return sentences

    @classmethod
    def _split_args(c, args):
        """
        Given args with a comma delimited query,
        split into n arg_sets, 1 for each query,
        in order to be able to make n separate queries
        that each know about all of the args.
        """
        # Split into queries
        queries = [q.strip() for q in args.get("query").split(",")]
        # To be sure we are not mutating args...
        tags_args = args.copy()
        tags_args.pop("query")
        args_list = [tags_args.copy() for q in queries]
        [a.update({"query": queries[i]})for i, a in enumerate(args_list)]

        return (queries, args_list)

    def _es_update_callback(self):
        # NEED TO FORCE REFRESH SO NEXT QUERY IS ACCURATE
        # - elasticsearch is known to take a second to update
        # (possibly a caching type issue?), so we force refresh
        es.indices.refresh(index="corpus")

class Graph():
    def __init__(self, x, labels, data):
        # Should be the years
        self.x = x
        # Should be the queries
        self.labels = labels
        # x axis labels, by # bars per label
        # aka, queries x years
        self.data = data
        self.figure = None
        self.figure = self.figure if self.figure else self._make_figure()

    def _make_figure(self):
        width = .1
        fig=plt.figure()
        ax=fig.add_subplot(111)

        idx = np.arange(len(self.x))

        for i, d in enumerate(self.data):
            coords = [i*width+j for j in range(len(d))]
            ax.bar(coords, height=d, width=width, align='center')

        plt.legend(self.labels, loc='upper right')
        ax.set_xticks([x + width for x in idx])
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

    def save_PDF(self, fn):
        pdf_path = settings.CORPORA_DIR + fn + '.pdf'
        f = self.figure

        pp = PdfPages(pdf_path)
        pp.savefig(f)
        pp.close()

        return pdf_path

    def save_PNG(self, fn):
        png_path = settings.CORPORA_DIR + fn + '.png'
        f = self.figure
        FigureCanvas(f)
        f.savefig(png_path)

        return png_path

    def save_as(self, fn, f_type):
        if f_type.lower() == "pdf":
            return self.save_PDF(fn)
        elif f_type.lower() == "png":
            return self.save_PNG(fn)
        else:
            raise Exception("Unimplemented filetype: %s" % f_type)


def matches_query(text, query):
    """
    Need to check (again) if the tag content matches
    the original string query.

    As we expose more options to the user, this will need to be updated
    with those options. E.g. regex, case sensitive, etc.
    """
    return query.lower() in text.lower()
