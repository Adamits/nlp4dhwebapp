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
        """
        es = Elasticsearch([settings.ES_URL])
        max_examples_dict = {"size": args.get("max_examples")} if args.get("max_examples") else {}
        # If there is SRL in the query, For each SRL,
        # search the query in the role
        # This will look for role OR role...etc
        if args.get('srl'):
            inner_hits_dict = max_examples_dict
            s = Search(using=es).query("nested", path="sentences",
                query=Q("nested", path="sentences.textSpans",
                        query=Q("multi_match", type="phrase",\
                                query=args.get("query"),
                                fields=["sentences.textSpans.srl.%s.content"\
                                    % r for r in args.get('srl')],
                        ),
                    inner_hits=inner_hits_dict
                    ),
                inner_hits=inner_hits_dict
                )
        else:
            inner_hits_dict = {'highlight': {'fields': {'sentences.content': {}}},
                            "size": args.get("max_examples")}
            inner_hits_dict.update(max_examples_dict)
            # Otherwise create the query with phrase search on the content
            s = Search(using=es).query("nested", path="sentences",
                query=Q("match_phrase", sentences__content=args.get("query")),
                inner_hits=inner_hits_dict)

        return es.search(index="corpus", body=s.to_dict(), size=args.get("max_examples"))

class Analyzer():
    def __init__(self, text_spans, query):
        self.text_spans = text_spans
        self.query = query

    def get_statistics():
        pass