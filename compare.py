from cmath import nan
from tkinter import SEPARATOR
from octokit import Octokit

import hmac, json, re
from config import config
from database import Connection

import numpy as np
from compareAlgorithms.tfidf import *


repo = ''
owner = ''

SEPARATOR = ';ç;'

octokit = Octokit(auth='installation', app_id=config['GITHUB']['APP_IDENTIFIER'], private_key=config['GITHUB']['PRIVATE_KEY'])

data = octokit.search.issues_and_pull_requests(q=f'repo:{repo}/{owner} state:open is:issue', per_page=100).json
issuesList = data['items']
total = data['total_count']

page = 2
while len(issuesList) != total:
  data = octokit.search.issues_and_pull_requests(q=f'repo:{repo}/{owner} state:open is:issue', per_page=100, page=page).json
  try:
    issuesList.extend(data['items'])
    page += 1
  except:
    break

db = Connection()

sql = f"select issue_id, issue_number, repo, owner, title from issues where title is not null and deleted_at is null"
issues_data = db.read(sql)
corpus = list(map(lambda x: str(x[4]), issues_data))


last = len(corpus)


corpus.append(None)
medianOfMedians = []

with open('out.csv','w+', encoding="utf-8") as f:
  topN = 3
  column = [0 for _ in range(topN)]
  
  f.write(f'open-title{SEPARATOR}open-number')
  for i in range(topN):
    f.write(f'{SEPARATOR}open-title-top{i+1}{SEPARATOR}open-number-top{i+1}')
  f.write('\n')

  for issue in issuesList:
    title = issue['title']
    open_issue_number = issue['number']
    corpus[last] = title

    arr = lemmatization(corpus)

    f.write(f'{title}{SEPARATOR}{open_issue_number}')
    median = []
    for i in range(topN):
      result_idx = np.nanargmax(arr[last])
      close_number = str(issues_data[result_idx][1])
      most_similar_title = corpus[result_idx]
      similarity = arr[last][result_idx]
      if(similarity > 0.5):
        median.append(similarity)
        similarity = f"'{similarity}"
        f.write(f'{SEPARATOR}{most_similar_title}{SEPARATOR}{similarity}')
        column[i] += 1
      else:
        f.write(f'{SEPARATOR}-{SEPARATOR}0')

      arr[last][result_idx] = -1
    f.write('\n')
    if(len(median)):
      medianOfMedians.append(np.median(median))
  f.write(f"Mediana das medianas{SEPARATOR}'{np.median(medianOfMedians)}")
  for i in range(topN):
    f.write(f"{SEPARATOR}Top {i+1}{SEPARATOR}{column[i]}")
  f.write('\n')