import spacy
spacy.load('en_core_web_sm')
from spacy.lang.en import English
nlp = English()
nlp.add_pipe(nlp.create_pipe('sentencizer'))

class Sentence():
    def __init__(self, args, query_args, highlight_results, highlight=None):
        self.response_args = args
        self.sentence_args = args.get("_source")
        self.query_args = query_args
        self.content = self.sentence_args.get("content")
        self.highlight = highlight
        self.highlighted_content = self.content
        if highlight_results:
            self._apply_highlight()

    def _apply_highlight(self):
        """
        Get the automatically highlighted content from the ES query,
        or build highlighting in python, for tag queries
        """
        if self.highlight:
            # There should only be one, or None in the list
            # Return that one, or return None
            self.highlighted_content = ' '.join([s for s in \
                                            self.highlight.get("sentences.content")])
        else:
            sentence = nlp(self.content)
            matching_text_spans = TextSpan.get_text_spans_from_response(\
                                            self.response_args.get("inner_hits"))
            sentence_string = self._highlight_spans(matching_text_spans, sentence)
            self.highlighted_content = sentence_string

    def _highlight_spans(self, text_spans, sentence):
        """
        Automatically update the highlighted_content
        attribute with markup for highlighting this text_span

        Return: the spaCy sentence as a string with HTML highlighting applied
        """
        start_spans = [ts.span[0] for ts in text_spans]
        end_spans = [ts.span[1] for ts in text_spans]
        tags = [list(ts.srl.keys())[0] for ts in text_spans]
        # Get the highlighted string.
        sentence = self._highlight_text(start_spans, end_spans, tags, sentence)

        return sentence

    def _highlight_text(self, start_spans, end_spans, tags, text):
        """
        text: Must be a spaCy sentence or span

        Return: A string of text with HTML highlighting applied
        """
        return_text = []
        for i, t in enumerate(text):
            start_found=False
            if i in start_spans:
                # Apply the start of the highlight HTML
                tag_idx = start_spans.index(i)
                return_text.append("<em class='%s'>%s" % (tags[tag_idx], t.text))
                start_found=True
            if i in end_spans:
                # Apply the end of the highlight HTML
                if start_found:
                  return_text.append("</em>")
                else:
                  return_text.append(t.text + "</em>")
            if i not in start_spans + end_spans:
                # Otherwise just add the raw text back
                return_text.append(t.text)

        # TODO: this messes up some spacing due to tokenization.
        # To counteract, we either need annotate() in the nlp4dh library to
        # index by a dumb tokenization of .split(" "), OR find some way to
        # Join back into a text string accounting for the spaCy tokenizer.
        return ' '.join(return_text)

class TextSpan():
    def __init__(self, args):
        self.content = args.get("content")
        self.span = args.get("span")
        self.srl = args.get("srl")
        self.ner = args.get("ner")
        self.dep = args.get("dep")

    @classmethod
    def get_text_spans_from_response(c, response_args):
        """
        Expects ES response in the form of a list of textspan
        inner_hit dictionaries

        Return: a list of TextSpan objects that were described by the dicitonary
        """
        if response_args is not None:
            text_spans = []
            for text_spans_args in response_args.values():
                for text_span_args in text_spans_args["hits"]["hits"]:
                    text_spans.append(TextSpan(text_span_args["_source"]))

            return text_spans
        else:
            return []

    def get_srl_tags(self):
        if self.srl is not None:
            return list(self.srl.keys())
        else:
            return []

    def get_ner_tags(self):
        if self.ner is not None:
            return list(self.ner.keys())
        else:
            return []

    def get_dep_tags(self):
        if self.dep is not None:
            return list(self.dep.keys())
        else:
            return []

    def get_tags(self):
        return self.get_srl_tags() +\
                self.get_ner_tags() +\
                self.get_dep_tags()

    def get_tag_counts(self, tags):
        tags_dict = dict.fromkeys(tags, 0)
        for tag in self.get_tags():
            if tag in tags:
                tags_dict[tag] += 1

        return tags_dict
