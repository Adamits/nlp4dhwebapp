from django.conf import settings
import os

def get_corpora_names(folder=None):
    def prune_names(names):
        return [n for n in names if n.endswith('.txt')]

    return prune_names(os.listdir(settings.CORPORA_DIR))

def get_color(tag):
  """
  Hard-coded dictionary for getting colors by tag
  """
  color_dict= {
            "agent": "#a3a9fa",
            "patient": "#73F377",
            "theme": "#ee6d6d"
          }

  return color_dict.get(tag.lower())
