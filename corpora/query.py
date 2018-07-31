from elasticsearch_dsl import DocType, Search, Index, Text, Integer, Q
from elasticsearch import Elasticsearch, helpers
from django.conf import settings

class Query():
    @classmethod
    def generate(c, args):
        """
        args: the query arguments from the form

        Returns: the results of the form arguments
                 interpreted into an ES query

        NOTE: Need to rewrite to elegeantly handle the additon of tag types as they
        are added, e.g. NER, etc
        """
        es = Elasticsearch([settings.ES_URL])
        max_examples_dict = {"size": args.get("max_examples")} if args.get("max_examples") else {"size": 10**9}
        years = args.get("years")
        # If there is SRL in the query, For each SRL,
        # search the query in the role
        # This will look for role OR role...etc
        if args.get('srl'):
            s = c._get_srl_query(args, es, max_examples_dict)
        else:
            s = c._get_content_query(args, es, max_examples_dict)

        #print(s.to_dict())
        return es.search(index="corpus", body=s.to_dict(), size=max_examples_dict["size"])

    @classmethod
    def generate_count(c, args):
        """
        It is pretty unbelievable that there is no good way
        to get the termfrequency score from a document for a certain term without
        parsing a bunch of ugly strings in "exlpanation"...
        """
        es = Elasticsearch([settings.ES_URL])
        if args.get('srl'):
            pass
        else:
            s = Search(using=es)
            s = s.from_dict({"explain": "true"})
            #term_statistics="true"
            s = s.query("nested", path="sentences",
                query=Q("match_phrase",
                        sentences__content=args.get("query"),
                ),
                inner_hits={}
            )

        return es.mtermvectors(index="corpus", body=s.to_dict(), term_statistics="true")

    @classmethod
    def is_aggregation_query(c, args):
        """
        Check if this query is asking for an aggregation

        right now we only aggregate by year..
        """
        return True if args.get("years") else False


    @classmethod
    def generate_aggregate_query(c, args):
        """
        Generate a similar query to generate(), but aggregate by years.
        This can be updated to aggregate by other factors, but for now only need
        years.
        """
        es = Elasticsearch([settings.ES_URL])
        max_examples_dict = {"size": args.get("max_examples")} if args.get("max_examples") else {"size": 10**9}
        years = args.get("years")
        # If there is SRL in the query, For each SRL,
        # search the query in the role
        # This will look for role OR role...etc
        if args.get('srl'):
            s = c._get_srl_query(args, es, max_examples_dict)
        else:
            s = c._get_content_query(args, es, max_examples_dict)

        if years:
            years = [y.strip() for y in years.split(",")]
            s = s.query('terms', year=years)

        # This will likely not scale, but not sure how else to better
        # aggregate right now.. just setting size to some massive number..
        s.aggs.bucket('by_year', 'terms', field='year').bucket("all", "top_hits", size="200000")
        response = s.execute()

        return response.aggregations.to_dict()['by_year']['buckets']

    @classmethod
    def _get_srl_query(c, args, es, max_examples_dict):
        content_query = Q("match_phrase", sentences__textSpans__content=args.get("query"))
        srl_queries = [Q("exists", field="sentences.textSpans.srl.%s" % r) & content_query\
                            for r in args.get('srl')]
        inner_hits_dict = max_examples_dict

        s = Search(using=es).query("nested", path="sentences",
            query=Q("nested", path="sentences.textSpans",
                    query=Q('bool',
                            should=srl_queries),
                inner_hits=inner_hits_dict
            ),
            inner_hits=inner_hits_dict
        )

        return s

    @classmethod
    def _get_content_query(c, args, es, max_examples_dict):
        # Either fix to still return relevant textSpans, or need seperate querying
        # methods completely for if we want sentences or textSpans
        inner_hits_dict = {'highlight': {'fields': {'sentences.content': {}}}}
        inner_hits_dict.update(max_examples_dict)
        # Otherwise create the query with phrase search on the content
        s = Search(using=es).query("nested", path="sentences",
            query=Q("match_phrase",
                    sentences__content=args.get("query")
            ),
            inner_hits=inner_hits_dict
        )

        return s


class Analyzer():
    def __init__(self, text_spans, query):
        self.text_spans = text_spans
        self.query = query

    def get_statistics():
        pass
