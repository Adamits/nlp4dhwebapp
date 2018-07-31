from elasticsearch import Elasticsearch
import os
import json
from time import sleep

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPING_FILE = os.path.join(BASE_DIR, 'mappings/corpus_index_mapping.json')

if __name__=='__main__':
  es = Elasticsearch(["http://elasticsearch:9200"])
  with open(MAPPING_FILE) as f:
    mapping = json.load(f)

  r = ""
  # Try creating index 3 times
  i=0
  failed = True
  while failed and i < 3:
    try:
      r = es.indices.create(index='corpus', body=mapping)
      failed = False
    except:
      # If it errors, wait 6 seconds for server to bootup
      # and try again
      sleep(5)
      if i < 2:
        print("Attempting to create index again...")
    i+=1

  print(r)
