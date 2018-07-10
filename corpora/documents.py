from elasticsearch_dsl import DocType, Search, Index, Text, Integer, Q
from elasticsearch import Elasticsearch, helpers

from django.conf import settings
import sys
import os
sys.path.append(settings.NLP4DH_DIR)
from lib.annotations import make_annotation_json

from .query import Query, Analyzer
from .subdocuments import *

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
        text_spans = Corpus.search_text_spans(args)
        # Just SRL right now, until we add more filters to form.
        query_tags = args.get("srl")
        merged_tag_counts = dict.fromkeys(query_tags, 0)
        for ts in text_spans:
            for tag, val in ts.get_tag_counts(query_tags).items():
                merged_tag_counts[tag] += val

        return merged_tag_counts


def matches_query(text, query):
    """
    Need to check (again) if the tag content matches
    the original string query.

    As we expose more options to the user, this will need to be updated
    with those options. E.g. regex, case sensitive, etc.
    """
    return query.lower() in text.lower()
