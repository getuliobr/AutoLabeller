import json
from precision.average_precision import mapk
from compareAlgorithms.sbert import *
from compareAlgorithms.tfidf import *
from compareAlgorithms.word2vec import *
from compareAlgorithms.yake import *
from bs4 import BeautifulSoup
import requests

from octokit import Octokit

from config import config
import re

owner = config['DATAMINING']['OWNER']
repo = config['DATAMINING']['REPO']

print(f"Getting merged pull requests that solve issues in {owner}/{repo}...")

octokit = Octokit(auth='installation', app_id=config['GITHUB']['APP_IDENTIFIER'], private_key=config['GITHUB']['PRIVATE_KEY'])

data = octokit.search.issues_and_pull_requests(q=f'repo:{owner}/{repo} is:pr is:merged linked:issue', per_page=100).json
pullList = data['items']
total = data['total_count']
print(f"Total issues: {total}")

page = 2
while len(pullList) != total:
  print(f"Page: {page} - {len(pullList)}/{total}")
  data = octokit.search.issues_and_pull_requests(q=f'repo:{owner}/{repo} is:pr is:merged linked:issue', per_page=100, page=page).json
  try:
    pullList.extend(data['items'])
    page += 1
  except:
    break

filesInPR = {}

for pr in pullList:
  print(f"Getting pr {pr['title']} files")
  fetchedAll = False
  filesInThisPR = []
  page = 1
  while not fetchedAll and len(filesInThisPR) < 3000:
    files = octokit.pulls.list_files(owner=owner, repo=repo, pull_number=pr['number'], page=page, per_page=100).json
    if len(files) < 100:
      fetchedAll = True
    page += 1
    filesInThisPR.extend(list(map(lambda x: x['filename'], files)))

  filesInPR[pr['title']] = filesInThisPR

with open('./data/filesInPullRequest.json', 'w+', encoding="utf-8") as f:
  f.write(json.dumps(filesInPR))