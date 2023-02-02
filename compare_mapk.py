import json
import numpy as np
from compareAlgorithms.tfidf import *
from precision.average_precision import mapk

issues = {}
prs = {}

with open('./data/filesThatSolveIssue.json', encoding='utf8') as f:
  issues = json.load(f)

with open('./data/filesInPullRequest.json', encoding='utf8') as f:
  prs = json.load(f)

corpus = [pr for pr in prs]
last = len(corpus)
corpus.append(None)

topK = 5

actual = []
predicted = []

for issue in issues:
  corpus[last] = issue
  files = []
  arr = lemmatization(corpus)

  for i in range(topK):
    result_idx = np.nanargmax(arr[last])
    arr[last][result_idx] = -1

    files.extend(prs[list(prs.keys())[result_idx]])

  actual.append(issues[issue])
  predicted.append(files)

print(mapk(actual, predicted, k=topK))