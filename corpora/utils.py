from django.conf import settings
import os

def get_corpora_names(folder=None):
    def prune_names(names):
        return [n for n in names if n.endswith('.txt')]

    return prune_names(os.listdir(settings.CORPORA_DIR))
