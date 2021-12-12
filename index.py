from octokit import Octokit

from dotenv import dotenv_values
from flask import Flask, request, abort
import hmac

app = Flask(__name__)
config = dotenv_values(".env")

@app.before_request
def verify_webhook_signature():
  payload_raw = request.get_data()
  request.headers['X_HUB_SIGNATURE']
  their_signature_header = request.headers['X_HUB_SIGNATURE']
  method, their_digest = their_signature_header.split('=')

  key = bytes(config['GITHUB_WEBHOOK_SECRET'], 'utf8')

  our_digest = hmac.digest(key=key, msg=payload_raw, digest=method).hex()

  if not hmac.compare_digest(their_digest, our_digest):
    return abort(401)

@app.route('/event_handler', methods=['POST'])
def event_handler():
  octokit = Octokit(auth='installation', app_id=config['GITHUB_APP_IDENTIFIER'], private_key=config['GITHUB_PRIVATE_KEY'])
  payload = request.json

  if payload['action'] != 'opened':
    return abort(400)

  repo = payload['repository']['name']
  issue_number = payload['issue']['number']
  owner = payload['repository']['owner']['login']

  print(owner, issue_number, repo)

  octokit.issues.add_labels_to_an_issue(owner=owner, repo=repo, issue_number=issue_number, labels=["needs-response"])
  octokit.issues.create_comment(owner=owner, repo=repo, issue_number=issue_number, body="teste direto do python")
  return {'success': True}

app.run()