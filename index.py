from github import Github, GithubIntegration

from git import get_connection, git_integration, get_token

from flask import Flask, request, abort
import hmac
from config import config

from datetime import datetime, timedelta
from issues import get_issues

from compareAlgorithms.sbert import get_sbert_embeddings, getMostSimilar
from compareAlgorithms.filtered import get_filtered

from pymongo import MongoClient, DESCENDING

app = Flask(__name__)

app_id = config['GITHUB']['APP_IDENTIFIER']
app_key = config['GITHUB']['PRIVATE_KEY']

mongoClient = MongoClient(config['DATABASE']['CONNECTION_STRING'])
db = mongoClient[config['DATABASE']['NAME']]

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

    
  if (action == 'added' and 'repositories_added' in payload) or (action == 'created' and 'repositories' in payload):
    print(action)
    repositories = payload['repositories_added'] if action == 'added' else payload['repositories']
    closedDate = datetime.now() - timedelta(days=180)
    closedDate = closedDate.isoformat()
    for repo in repositories:
      repo = repo['full_name']
      owner, repo = repo.split('/')
      db[repo].insert_many(get_issues(owner, repo, date=closedDate))
      
  # if 'issue' in payload and action == 'opened':
    # insert_issue(payload['issue'])
    
  if 'issue' in payload and action == 'labeled':
    label = payload['label']
    if label['name'].lower() != 'good first issue':
      return {'success': True}
    
    owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']
    full_repo = f"{owner}/{repo_name}"
    git_connection = get_connection(owner, repo_name)
    
    repo = git_connection.get_repo(full_repo)
    
    issue = payload['issue']
    number = issue['number']
    createdAt = issue['created_at']
    
    daysBefore = datetime.strptime(createdAt, '%Y-%m-%dT%H:%M:%S%z')
    daysBefore = daysBefore - timedelta(days=180)

    formatQuery = {
      'closed_at': {
        '$lte': issue['created_at'],
        '$gte': daysBefore.strftime('%Y-%m-%d')
      },
      'files.0': {'$exists': True},
    }
    
    issuesClosedBeforeCursor = db[full_repo].find(formatQuery, no_cursor_timeout=True).sort('number', DESCENDING)
    corpus = {issue['number']: issue for issue in issuesClosedBeforeCursor}
    issuesClosedBeforeCursor.close()
    issue['filtered'] = get_filtered(issue)
    issue['sbert'] = get_sbert_embeddings(issue)
    corpus[number] = issue
    
    print(getMostSimilar(number, corpus))
  #   issue = repo.get_issue(number=issue_number)
    
  #   issue.add_to_labels("needs-response")
  #   issue.create_comment(f"Teste\n")
    
  return {'success': True}

app.run()