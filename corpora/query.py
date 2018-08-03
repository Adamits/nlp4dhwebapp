from elasticsearch_dsl import DocType, Search, Index, Text, Integer, Q
from elasticsearch import Elasticsearch, helpers
from django.conf import settings

"""
Wrapper over the ES query API. This is for running queries, which are
somewhat complicated in elasticsearch-py.
"""
class Query():
    def __init__(self, args):
        self.args = args
        self.es = Elasticsearch([settings.ES_URL])

    def _is_content_query(self):
        pass

    def _is_tag_query(self):
        """
        Only tag right now is SRL
        """
        return True if self.args.get('srl') else False

    def is_aggregation_query(self):
        """
        Check if this query is asking for an aggregation

        Basically, do we have values for whatever
        goes on the x axis? That is what we will aggregate by.
        """
        X = self.args.get("x_axis")
        # Just SRL for now, but eventually, tags will need to be
        # a list of all possible 'tag-types' to check if one is in the query
        X = ["srl"] if X=="tags" else [X]
        return True if any([self.args.get(x) for x in X]) else False

    def _make_search(self):
        max_examples_dict = {"size": self.args.get("max_examples")} \
            if self.args.get("max_examples") else {"size": 10**9}
        if self._is_tag_query():
            # Just SRL right now.
            s = self._get_srl_query(max_examples_dict)
        else:
            s = self._get_content_query(max_examples_dict)

        return s, max_examples_dict

    def generate(self):
        """
        Returns: the results of the form arguments
                 interpreted into an ES query

        NOTE: Need to rewrite to elegeantly handle the additon of tag types as they
        are added, e.g. NER, etc
        """
        s, max_examples_dict = self._make_search()

        #print(s.to_dict())
        return self.es.search(index="corpus", body=s.to_dict(), size=max_examples_dict["size"])

    def generate_aggregate_query(self, aggregate_by):
        """
        aggregate_by: the arg by which we are aggregating.

        Generate a similar query to generate(), but aggregate by some term.
        """
        s, max_examples_dict = self._make_search()
        if aggregate_by == "years":
            years = [y.strip() for y in self.args.get("years").split(",")]
            s = s.query('terms', year=years)
            # This will likely not scale, but not sure how else to better
            # aggregate right now.. just setting size to some massive number..
            s.aggs.bucket('by_years', 'terms', field='year').bucket("all", "top_hits", size="200000")

            response = s.execute()
            return response.aggregations.to_dict()['by_years']['buckets']
        elif aggregate_by == "tags":
            # This does not aggregate by SRL tags.
            # Not sure if its an issue with nested aggs
            # Or if an update to the schema is needed.
            # e.g. sentences.textSpans.srl points to a dict, and we want to
            # Aggregate by the keys to that dict. Maybe need a tags: [] field.
            s.aggs.bucket('sentences', 'nested', path='sentences')\
                .bucket('by_tags', 'terms', field='sentences.textSpans.srl')\
                .bucket("all", "top_hits", size="200000")

            response = s.execute()
            return response.aggregations.to_dict()['sentences']['by_tags']['buckets']
        else:
            raise Exception("No aggregation implemented for %s" % aggregate_by)


    def generate_count(self):
        """
        ***NOTE** This method does not yet work and is unused.

        It is pretty unbelievable that there is no good way
        to get the termfrequency score from a document for a certain term without
        parsing a bunch of ugly strings in "exlpanation"...
        """
        if self.args.get('srl'):
            pass
        else:
            s = Search(using=self.es)
            s = s.from_dict({"explain": "true"})
            #term_statistics="true"
            s = s.query("nested", path="sentences",
                query=Q("match_phrase",
                        sentences__content=self.args.get("query"),
                ),
                inner_hits={}
            )

        return self.es.mtermvectors(index="corpus", body=s.to_dict(), term_statistics="true")

    def _get_srl_query(self, max_examples_dict):
        """
        The SRL portion of a query.

        The search that is returned in the dsl api can be used in a larger query
        """
        # Content portion of the query to match in textSpan.content
        content_query = Q("match_phrase", sentences__textSpans__content=self.args.get("query"))
        # SRL part of the query, to check for content as the given SRL tag(s)
        srl_queries = [Q("exists", field="sentences.textSpans.srl.%s" % r) & content_query\
                            for r in self.args.get('srl')]
        inner_hits_dict = max_examples_dict

        s = Search(using=self.es).query("nested", path="sentences",
            query=Q("nested", path="sentences.textSpans",
                    query=Q('bool',
                            should=srl_queries),
                inner_hits=inner_hits_dict
            ),
            inner_hits=inner_hits_dict
        )

        return s

    def _get_content_query(self, max_examples_dict):
        """
        The content (e.g. query terms) portion of a query.

        The search that is returned in the dsl api can be used in a larger query
        """
        # Either fix to still return relevant textSpans, or need seperate querying
        # methods completely for if we want sentences or textSpans
        inner_hits_dict = {'highlight': {'fields': {'sentences.content': {}}}}
        inner_hits_dict.update(max_examples_dict)
        # Otherwise create the query with phrase search on the content
        s = Search(using=self.es).query("nested", path="sentences",
            query=Q("match_phrase",
                    sentences__content=self.args.get("query")
            ),
            inner_hits=inner_hits_dict
        )

        return s


class Analyzer():
    def __init__(self, args):
        pass

    def get_statistics():
        pass
