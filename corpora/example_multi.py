"""
Here statically as an example of a multimatch so i don't forget...
"""
Q("multi_match", type="phrase",\
        query=args.get("query"),
        fields=["sentences.textSpans.srl.%s.content"\
            % r for r in args.get('srl')],
