import json
import numpy as np
from compareAlgorithms.tfidf import lemmatization
from compareAlgorithms.yake import yake
from compareAlgorithms.word2vec import word2vec
from compareAlgorithms.sbert import sbert
from precision.average_precision import mapk

issues = {}
prs = {}

with open('./data/filesThatSolveIssue.json', encoding='utf-8') as f:
  issues = json.load(f)

with open('./data/filesInPullRequest.json', encoding='utf-8') as f:
  prs = json.load(f)

corpus = [pr for pr in prs]
last = len(corpus)
corpus.append(None)

topK = 5

actual = []
predicted = []

print('Calculating similarities')
j = 0
for issue in issues:
  j += 1
  print(f'{j}/{len(issues)} - {issue}')
  files = []
  
  # corpus[last] = issue
  # arr = lemmatization(corpus)
  # for i in range(topK):
  #   result_idx = np.nanargmax(arr[last])
  #   arr[last][result_idx] = -1
  #   files.extend(prs[list(prs.keys())[result_idx]])
  
  prs_data = [[0,0,0,0, pr] for pr in prs ]
  sb = sbert(prs_data, issue)
  ordered_sb = sorted(sb, key=lambda x: x[4], reverse=True)
  for i in range(topK):
    files.extend(prs[ordered_sb[i][3]])

  # prs_data = [[0,0,0,0, pr] for pr in prs ]
  # w2v = word2vec(prs_data, issue)
  # ordered_w2v = sorted(w2v, key=lambda x: x[4], reverse=True)
  # for i in range(topK):
  #   files.extend(prs[ordered_w2v[i][3]])

  actual.append(issues[issue])
  predicted.append(list(set(files)))

print('Calculating MAP@K')
print(mapk(actual, predicted, k=topK))