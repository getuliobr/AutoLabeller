from asyncio.windows_events import NULL
from unittest import result
from github import Github, GithubIntegration

from flask import Flask, request, abort
import hmac, json
from config import config
from database import Connection

from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np  

app = Flask(__name__)
db = Connection()

app_id = config['GITHUB']['APP_IDENTIFIER']
app_key = config['GITHUB']['PRIVATE_KEY']

git_integration = GithubIntegration(
  app_id,
  app_key
)

@app.before_request
def verify_webhook_signature():
  payload_raw = request.get_data()
  request.headers['X_HUB_SIGNATURE']
  their_signature_header = request.headers['X_HUB_SIGNATURE']
  method, their_digest = their_signature_header.split('=')
  key = bytes(config['GITHUB']['WEBHOOK_SECRET'], 'utf8')

  our_digest = hmac.digest(key=key, msg=payload_raw, digest=method).hex()

  if not hmac.compare_digest(their_digest, our_digest):
    return abort(401)

@app.route('/event_handler', methods=['POST'])
def event_handler():
  payload = request.json

  action = payload['action']
  repo_name = payload['repository']['name']
  owner = payload['repository']['owner']['login']
  issue_number = payload['issue']['number']
  issue_id = payload['issue']['id']
  title = payload['issue']['title']
  body = payload['issue']['body']
  author = payload['issue']['user']['login']

  git_connection = Github(
    login_or_token=git_integration.get_access_token(
      git_integration.get_installation(owner, repo_name).id
    ).token
  )
  repo = git_connection.get_repo(f"{owner}/{repo_name}")
  issue = repo.get_issue(number=issue_number)

  if action == 'opened':
    try:
      #FIXME: fix no suggestion when nothing is similar
      sql = f"insert into issues(issue_id, issue_number, repo, \"owner\", title, author, body, status, created_at) values (%s, %s, %s, %s, %s, %s, %s, 'open', current_timestamp)"
      values = (issue_id, issue_number, repo_name, owner, title, author, body, )
      db.write(sql, values)

      if title:
        sql = f"select issue_id, issue_number, repo, owner, title from issues where title is not null and deleted_at is null"
        issues_data = db.read(sql)
        issues_titles = list(map(lambda x: str(x[4]), issues_data))

        # https://stackoverflow.com/questions/8897593/how-to-compute-the-similarity-between-two-text-documents
        tfidf = TfidfVectorizer().fit_transform(issues_titles)
        pairwise_similarity = tfidf * tfidf.T

        arr = pairwise_similarity.toarray()
        np.fill_diagonal(arr, np.nan)
        input_idx = issues_titles.index(title)
        result_idx = np.nanargmax(arr[input_idx])

        issue_data = issues_data[result_idx]

        near_issue_id, near_issue_number, near_repo, near_owner, near_title = issue_data

        issue.add_to_labels("needs-response")
        issue.create_comment(f"Titulo mais parecido: {near_title}\nNo repositorio {near_repo} o issue tem o numero: {near_issue_number}")
    except Exception as e:
      print(e)
      return abort(500)
  elif action == 'assigned':
    assignee = payload['assignee']['login']
    try:
      sql = f"insert into assigned(issue_id,\"user\",created_at) values (%s, %s, current_timestamp)"
      values = (issue_id, assignee,)
      db.write(sql, values)
    except:
      return abort(500)
  elif action == 'unassigned':
    assignee = payload['assignee']['login']
    try:
      sql = f"update assigned set deleted_at = current_timestamp where issue_id = %s and \"user\" = %s"
      values = (issue_id, assignee,)
      db.write(sql, values)
    except:
      return abort(500)
  elif action == 'closed' or action == 'reopened':
    try:
      sql = f"update issues set status = %s, updated_at = current_timestamp where issue_id = %s"
      values = (action, issue_id,)
      db.write(sql, values)
    except:
      return abort(500)
  elif action == 'deleted':
    try:
      sql = f"update issues set deleted_at = current_timestamp where issue_id = %s"
      values = (issue_id,)
      db.write(sql, values)
    except:
      return abort(500)
  else:
    print(action)
    return abort(400)
  return {'success': True}

app.run()