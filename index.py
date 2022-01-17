from octokit import Octokit

from flask import Flask, request, abort
import hmac, json
from config import config
from database import Connection

app = Flask(__name__)
db = Connection()

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
  octokit = Octokit(auth='installation', app_id=config['GITHUB']['APP_IDENTIFIER'], private_key=config['GITHUB']['PRIVATE_KEY'])
  payload = request.json

  action = payload['action']
  repo = payload['repository']['name']
  owner = payload['repository']['owner']['login']
  issue_number = payload['issue']['number']
  issue_id = payload['issue']['id']
  title = payload['issue']['title']
  body = payload['issue']['body']
  body = f"'{body}'" if body else 'NULL'
  author = payload['issue']['user']['login']

  print(action)

  if action == 'opened':
    try:
      sql = f"insert into issues(issue_id, issue_number, repo, \"owner\", title, author, body, status, created_at) values ({issue_id}, {issue_number}, '{repo}', '{owner}', '{title}', '{author}', {body}, 'open', current_timestamp)"
      db.query(sql)
    except:
      return abort(500)

    octokit.issues.add_labels_to_an_issue(owner=owner, repo=repo, issue_number=issue_number, labels=["needs-response"])
    octokit.issues.create_comment(owner=owner, repo=repo, issue_number=issue_number, body="teste direto do python")
  elif action == 'assigned':
    assignee = payload['assignee']['login']
    try:
      sql = f"insert into assigned(issue_id,\"user\",created_at) values ({issue_id}, '{assignee}', current_timestamp)"
      db.query(sql)
    except:
      return abort(500)
  elif action == 'unassigned':
    assignee = payload['assignee']['login']
    try:
      sql = f"update assigned set deleted_at = current_timestamp where issue_id = {issue_id} and \"user\" = '{assignee}'"
      db.query(sql)
    except:
      return abort(500)
  elif action == 'closed' or action == 'reopened':
    try:
      sql = f"update issues set status = '{action}', updated_at = current_timestamp where issue_id = {issue_id}"
      db.query(sql)
    except:
      return abort(500)
  elif action == 'deleted':
    try:
      sql = f"update issues set deleted_at = current_timestamp where issue_id = {issue_id}"
      db.query(sql)
    except:
      return abort(500)
  else:
    return abort(400)
  return {'success': True}

app.run()