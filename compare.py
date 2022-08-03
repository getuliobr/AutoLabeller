from tkinter import SEPARATOR
from octokit import Octokit

import json, csv
from config import config

import numpy as np
from compareAlgorithms.tfidf import *


owner = ''
repo = ''

DELIMITER = ';'
QUOTE = "'"

jsonIssues = {}

with open('issues.json', encoding='utf8') as f:
  jsonIssues = json.load(f)

open_issues_iterator = filter(lambda x: x['issue_data']['state'] == 'open' and not 'pull_request' in x['issue_data'], jsonIssues)

open_issues = list(open_issues_iterator)

octokit = Octokit(auth='installation', app_id=config['GITHUB']['APP_IDENTIFIER'], private_key=config['GITHUB']['PRIVATE_KEY'])

data = octokit.search.issues_and_pull_requests(q=f'repo:{repo}/{owner} state:closed linked:pr is:issue', per_page=100).json
closed_linked_issues = data['items']

total = data['total_count']
total = total if total <= 1000 else 1000

page = 2
while len(closed_linked_issues) < total:
  data = octokit.search.issues_and_pull_requests(q=f'repo:{repo}/{owner} state:closed linked:pr is:issue', per_page=100, page=page).json
  try:
    closed_linked_issues.extend(data['items'])
    page += 1
  except:
    break

corpus = list(map(lambda x: x['title'], closed_linked_issues))
last = len(corpus)
corpus.append(None)

with open('out.csv','w+', encoding="utf-8", newline='') as f:
  writer = csv.writer(f, delimiter=DELIMITER, quotechar=QUOTE, quoting=csv.QUOTE_ALL)

  topN = 3
  
  header = ['open-title','open-number']

  for i in range(topN):
    header.extend([f'closed-title-top{i+1}', f'closed-number-top{i+1}', f'closed-similarity-top{i+1}'])

  writer.writerow(header)

  for issue in open_issues:
    issue = issue['issue_data']
    title = issue['title']
    open_issue_number = issue['number']
    corpus[last] = title

    arr = lemmatization(corpus)

    data = [title, open_issue_number]

    for i in range(topN):
      result_idx = np.nanargmax(arr[last])
      similar_close_number = str(closed_linked_issues[result_idx]['number'])
      similar_title = corpus[result_idx]
      similarity = arr[last][result_idx]

      data.extend([similar_title, similar_close_number, similarity])

      arr[last][result_idx] = -1

    writer.writerow(data)