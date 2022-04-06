from cmath import nan
from octokit import Octokit

import hmac, json, re
from config import config
from database import Connection

from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np  


repo = ''
owner = ''

octokit = Octokit(auth='installation', app_id=config['GITHUB']['APP_IDENTIFIER'], private_key=config['GITHUB']['PRIVATE_KEY'])

data = octokit.search.issues_and_pull_requests(q=f'repo:{repo}/{owner} state:open is:issue', per_page=100).json
issuesList = data['items']
total = data['total_count']

page = 2
while len(issuesList) != total:
  data = octokit.search.issues_and_pull_requests(q=f'repo:{repo}/{owner} state:open is:issue', per_page=100, page=page).json
  try:
    issuesList.extend(data['items'])
    page += 1
  except:
    break

db = Connection()

sql = f"select issue_id, issue_number, repo, owner, title from issues where title is not null and deleted_at is null"
issues_data = db.read(sql)
corpus = list(map(lambda x: str(x[4]), issues_data))


last = len(corpus)


corpus.append(None)

with open('out.csv','w+', encoding="utf-8") as f:
  f.write('open-title;ç;open-number;ç;close-title;ç;similarity;ç;close-title;ç;similarity;ç;close-title;ç;similarity\n')
  print(len(issuesList))
  for issue in issuesList:
    title = issue['title']
    open_issue_number = issue['number']
    corpus[last] = title

    tfidf = TfidfVectorizer().fit_transform(corpus)
    pairwise_similarity = tfidf * tfidf.T

    arr = pairwise_similarity.toarray()
    np.fill_diagonal(arr, np.nan)

    f.write(f'{title};ç;{open_issue_number}')
    for i in range(3):
      result_idx = np.nanargmax(arr[last])
      close_number = str(issues_data[result_idx][1])
      most_similar_title = corpus[result_idx]
      similarity = arr[last][result_idx]
      if(similarity):
        similarity = str(similarity).replace('.',',')[:8]
        f.write(f';ç;{most_similar_title};ç;{similarity}')
      else:
        f.write(f';ç;-;ç;0')

      arr[last][result_idx] = -1
    f.write('\n')