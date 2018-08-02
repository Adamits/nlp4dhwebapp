"""
A CountsFile is specifically the counts of query/tag combinations that
can be output in a tsv format in a txt file.
"""
from .corpus import Corpus

class CountsFile:
    def __init__(self, args):
        self.args = args
        self.dict_counts = {}
        self.str = ""

    def save(self, fn):
        """
        fn: the file path to where the txt file should be saved.

        Saves the counts str to the specified fn
        """
        with open(fn, "w") as f:
            f.write(self.str)

    def make_counts(self):
        """
        Set self.dict_counts to a dictionary of query term, tag counts
        Set self.str to the string format of that same data.
        """
        self.dict_counts = Corpus.count_text_spans_by_query(self.args)
        self.str = self._prepare_string(self.dict_counts)

    def _prepare_string(self, d):
        """
        d: A dicitonary of the format {query_term: {tag: count, tag: count}, ...}

        Return: A formatted string to be written to a text file
        """
        out = ""
        DELIMITER = "\t"
        header = DELIMITER.join(["query"] + \
            list(set([t for tags in d.values() for t in tags.keys()])))
        out = header + "\n"
        for q in d.keys():
            out += q + DELIMITER
            out += "\t".join([str(v) for t, v in d[q].items()])
            out += "\n"

        return out

def matches_query(text, query):
    """
    Need to check (again) if the tag content matches
    the original string query.

    As we expose more options to the user, this will need to be updated
    with those options. E.g. regex, case sensitive, etc.
    """
    return query.lower() in text.lower()
