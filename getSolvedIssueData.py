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

repo = ''
owner = ''

octokit = Octokit(auth='installation', app_id=config['GITHUB']['APP_IDENTIFIER'], private_key=config['GITHUB']['PRIVATE_KEY'])

data = octokit.search.issues_and_pull_requests(q=f'repo:{repo}/{owner} state:closed linked:pr is:issue', per_page=100).json
issuesList = data['items']
total = data['total_count']
print(f"Total issues: {total}")

page = 2
while len(issuesList) != total:
  print(f"Page: {page} - {len(issuesList)}/{total}")
  data = octokit.search.issues_and_pull_requests(q=f'repo:{repo}/{owner} state:closed linked:pr is:issue', per_page=100, page=page).json
  try:
    issuesList.extend(data['items'])
    page += 1
  except:
    break

filesThatSolveIssue = {}

for issue in issuesList:
  print(f"Getting issue {issue['html_url']}")
  r = requests.get(issue['html_url'])

  soup = BeautifulSoup(r.text, 'html.parser')
  issueForm = soup.find("form", { "aria-label": re.compile('Link issues')})

  linkedMergedPR = [f"https://github.com{i.parent['href']}" for i in issueForm.find_all('svg', attrs={ "aria-label": re.compile('Merged Pull Request')})]

  filesSolvingThisIssue = []

  for pr in linkedMergedPR:
    print(f"Getting pull request {pr} files")
    fetchedAll = False
    filesInThisPR = []
    while not fetchedAll and len(filesInThisPR) < 3000:
      files = octokit.pulls.list_files(owner=owner, repo=repo, pull_number=pr.split('/')[-1], per_page=100).json
      if len(files) < 100:
        fetchedAll = True
      filesInThisPR.extend(list(map(lambda x: x['filename'], files)))
    filesSolvingThisIssue.extend(filesInThisPR)
  
  filesThatSolveIssue[issue['title']] = filesSolvingThisIssue

with open('filesThatSolveIssue.json', 'w+', encoding="utf-8") as f:
  f.write(json.dumps(filesThatSolveIssue))