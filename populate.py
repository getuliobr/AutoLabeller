from octokit import Octokit

import hmac, json, re
from config import config
from database import Connection

repo = ''
owner = ''

octokit = Octokit(auth='installation', app_id=config['GITHUB']['APP_IDENTIFIER'], private_key=config['GITHUB']['PRIVATE_KEY'])

data = octokit.search.issues_and_pull_requests(q=f'repo:{repo}/{owner} state:closed linked:pr is:issue', per_page=100).json
issuesList = data['items']
total = data['total_count']

page = 2
while len(issuesList) != total:
  data = octokit.search.issues_and_pull_requests(q=f'repo:{repo}/{owner} state:closed linked:pr is:issue', per_page=100, page=page).json
  try:
    issuesList.extend(data['items'])
    page += 1
  except:
    break

db = Connection()

sql = f"insert into issues(issue_id, issue_number, repo, \"owner\", title, author, body, status, created_at) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
for issue in issuesList:
  issue_id = issue['id']
  issue_number = issue['number']
  title = issue['title']
  author = issue['user']['login']
  body = issue['body']
  status = issue['state']
  created_at = issue['created_at']

  values = ( issue_id, issue_number, repo, owner, title, author, body, status, created_at, )

  db.write(sql, values)
