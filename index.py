from git import get_connection

from flask import Flask, request, abort
import hmac
from config import config

from datetime import datetime, timedelta
from issues import get_issues, get_issue_by_closed

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

def insert_issues(db, issues):
  for issue in issues:
    db.update_one({'number': issue['number']}, {'$set': issue}, upsert=True)

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
      repoFullname = repo['full_name']
      owner, repo = repoFullname.split('/')
      issues = get_issues(owner, repo, date=closedDate)
      insert_issues(db[repoFullname], issues)
      
  if 'issue' in payload and action == 'closed':
    repoFullname = payload['repository']['full_name']
    owner, repo = repoFullname.split('/')
    issue = payload['issue']    
    closedDate = issue['closed_at']
    
    closedDate = datetime.strptime(closedDate, '%Y-%m-%dT%H:%M:%S%z') - timedelta(seconds=1)
    
    if issue['state_reason'] == 'completed':
      issues = get_issue_by_closed(owner, repo, closed_at=closedDate.isoformat())
      insert_issues(db[repoFullname], issues)
    
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
        '$gte': daysBefore.isoformat()
      },
      'files.0': {'$exists': True},
    }
    
    corpus = {
      _issue['number']: _issue for _issue in db[full_repo].find(formatQuery).sort('number', DESCENDING)
    }
    
    issue['filtered'] = get_filtered(issue)
    issue['sbert'] = get_sbert_embeddings(issue)
    corpus[number] = issue
    
    recNumber, similarity = getMostSimilar(number, corpus)
    
    issue = repo.get_issue(number=number)
    comment = f'To solve this issue, look at this recommendation:\n - https://github.com/{full_repo}/issues/{recNumber} similarity: {(similarity)*100:.2f}'
    issue.create_comment(comment)
    
  return {'success': True}

app.run()