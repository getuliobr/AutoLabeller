from github import Github, GithubIntegration

from flask import Flask, request, abort
import hmac
from config import config
from database import Connection
import re

from compareAlgorithms.tfidf import lemmatization
from compareAlgorithms.yake import yake
from compareAlgorithms.word2vec import word2vec
from compareAlgorithms.sbert import sbert

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
  
  git_connection = Github(
    login_or_token=git_integration.get_access_token(
      git_integration.get_installation(owner, repo_name).id
    ).token
  )
  repo = git_connection.get_repo(f"{owner}/{repo_name}")
  
  if 'pull_request' in payload:
    pr = payload['pull_request']
    pr_id = pr['id']
    pr_number = pr['number']
    title = pr['title']
    body = pr['body']
    author = pr['user']['login']
    state = pr['state']

    pr = repo.get_pull(number=pr_number)
    
    if action == 'opened':
      try:
        print(action, 'teste')
        sql = f"insert into pullrequest(pr_id, pr_number, repo, \"owner\", title, author, body, status, created_at) values (%s, %s, %s, %s, %s, %s, %s, %s, current_timestamp)"
        values = (pr_id, pr_number, repo_name, owner, title, author, body, state,)
        db.write(sql, values)
      except Exception as e:
        print(e)
        return abort(500)
    elif action == 'deleted':
      try:
        sql = f"update pullrequest set deleted_at = current_timestamp where pr_id = %s"
        values = (pr_id,)
        db.write(sql, values)
      except:
        return abort(500)
    # Check if it mentions another pr or issue
    if body and action != 'deleted':
      regex = r"#([0-9]+)"
      issues = re.findall(regex, body)
      if len(issues):
        values = [repo_name, owner,]
        values.extend(issues)
        print(values)
        placeholder = '%s'
        placeholder = ', '.join(placeholder for _ in issues)
        sql = f"select issue_id from issues where repo = %s and owner = %s and deleted_at is null and issue_number in ({placeholder})"
        issues_data = db.read(sql, tuple(values))
        for issue in issues_data:
          issue_id = issue[0]
          sql = f"insert into connection(pr_id, issue_id) values (%s, %s)"
          values = (pr_id, issue_id,)
          db.write(sql, values)
    else:
      print(action)
      return abort(400)
  if 'issue' in payload:
    issue = payload['issue']
    issue_number = issue['number']
    issue_id = issue['id']
    title = issue['title']
    body = issue['body']
    author = issue['user']['login']
    state = issue['state']

    issue = repo.get_issue(number=issue_number)

    if action == 'opened':
      try:
        #FIXME: fix no suggestion when nothing is similar
        sql = f"insert into issues(issue_id, issue_number, repo, \"owner\", title, author, body, status, created_at) values (%s, %s, %s, %s, %s, %s, %s, %s, current_timestamp)"
        values = (issue_id, issue_number, repo_name, owner, title, author, body, state,)
        db.write(sql, values)
        if title:
          sql = f"select issue_id, issue_number, repo, owner, title from issues where title is not null and deleted_at is null"
          issues_data = db.read(sql)
          issues_titles = list(map(lambda x: str(x[4]), issues_data))

          input_idx = None
          for idx, issue_title in enumerate(issues_titles):
            if issue_title == title:
              input_idx = idx
              break

          if input_idx is None:
            return abort(500)

          arr = lemmatization(issues_titles)
          result_idx = np.nanargmax(arr[input_idx])

          issue_data = issues_data[result_idx]

          near_issue_id, near_issue_number, near_repo, near_owner, near_title = issue_data

          keywords = yake(title)
          ordered_keywords = sorted(keywords, key=lambda x: x[1], reverse=True)
          max_keywords = list(map(lambda x: f'{x[0]}: {x[1]}', ordered_keywords[:5]))

          max_keywords = ', '.join(max_keywords)

          w2v = word2vec(issues_data, title)
          ordered_w2v = sorted(w2v, key=lambda x: x[4], reverse=True)
          max_w2v = list(map(lambda x: f'Numero {x[0]} no {x[1]}/{x[2]}, titulo: "{x[3]}" similaridade: {x[4]}', ordered_w2v[:5]))
          max_w2v = '\n'.join(max_w2v)

          sb = sbert(issues_data, title)
          ordered_sb = sorted(sb, key=lambda x: x[4], reverse=True)
          max_sb = list(map(lambda x: f'Numero {x[0]} no {x[1]}/{x[2]}, titulo: "{x[3]}" similaridade: {x[4]}', ordered_sb[:5]))
          max_sb = '\n'.join(max_sb)

          issue.add_to_labels("needs-response")
          issue.create_comment(f"Titulo mais parecido: {near_title}\nNo repositorio {near_repo} o issue tem o numero: {near_issue_number}\nPalavras mais relevantes de acordo com o yake: {max_keywords}\nTitulos mais similares de acordo com word2vector:\n{max_w2v}\nTitulos mais similares de acordo com sbert:\n{max_sb}:\n")
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