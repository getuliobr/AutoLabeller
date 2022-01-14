from octokit import Octokit

from flask import Flask, request, abort
import hmac, json
from config import config

app = Flask(__name__)

@app.before_request
def verify_webhook_signature():
  payload_raw = request.get_data()
  request.headers['X_HUB_SIGNATURE']
  their_signature_header = request.headers['X_HUB_SIGNATURE']
  method, their_digest = their_signature_header.split('=')
  print(config['GITHUB']['WEBHOOK_SECRET'])
  key = bytes(config['GITHUB']['WEBHOOK_SECRET'], 'utf8')

  our_digest = hmac.digest(key=key, msg=payload_raw, digest=method).hex()

  if not hmac.compare_digest(their_digest, our_digest):
    return abort(401)

@app.route('/event_handler', methods=['POST'])
def event_handler():
  octokit = Octokit(auth='installation', app_id=config['GITHUB']['APP_IDENTIFIER'], private_key=config['GITHUB']['PRIVATE_KEY'])
  payload = request.json

  if payload['action'] != 'opened':
    return abort(400)

  repo = payload['repository']['name']
  owner = payload['repository']['owner']['login']
  issue_number = payload['issue']['number']
  body = payload['issue']['body']

  print(owner, issue_number, repo, body)

  octokit.issues.add_labels_to_an_issue(owner=owner, repo=repo, issue_number=issue_number, labels=["needs-response"])
  octokit.issues.create_comment(owner=owner, repo=repo, issue_number=issue_number, body="teste direto do python")
  return {'success': True}

app.run()