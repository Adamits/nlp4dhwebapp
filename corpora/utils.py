from django.conf import settings
import os
import colorsys

def get_corpora_names(folder=None):
    """
    Gets a list of the corpora (text file) names from the
    shared data dir.
    """
    def prune_names(names):
        return [n for n in names if n.endswith('.txt')]

    return prune_names(os.listdir(settings.CORPORA_DIR))
