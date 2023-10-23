import datetime
from string import digits
import pymongo
from config import config
from github import Github, GithubIntegration
from queries import SearchIssues
import re
from sentence_transformers import SentenceTransformer, util
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

app_id = config['GITHUB']['APP_IDENTIFIER']
app_key = config['GITHUB']['PRIVATE_KEY']

git_integration = GithubIntegration(
  app_id,
  app_key
)

owner = ''
repo_name = ''

git_connection = Github(
    login_or_token=git_integration.get_access_token(
      git_integration.get_installation(owner, repo_name).id
    ).token
  )

repo = git_connection.get_repo(f"{owner}/{repo_name}")
regex = r": ([^\/]+)\/([^#]+)#([0-9]+)"

mongoClient = pymongo.MongoClient(config['MONGODB']['CONNECTION_STRING'])
db = mongoClient['REAL_RUN']
collection = db['issues']

totalIssues = git_connection.search_issues('repo:jabref/jabref is:issue is:closed linked:pr').totalCount
currDate = '2000-01-01T00:00:00Z'

issueList = []
while(len(issueList) != totalIssues):
  issueList.extend(SearchIssues('jabref', 'jabref', currDate))
  currDate = issueList[-1]['createdAt']

def PossibleSuggestions(currIssue):
  returnIssues = []
  
  daysPrior = currIssue['parsedCreatedAt'] - datetime.timedelta(days=90)
  for issue in issueList:   
    if issue['parsedClosedAt'] >= currIssue['parsedCreatedAt'] or issue['parsedCreatedAt'] >= currIssue['parsedCreatedAt']:
      continue
    
    if issue['parsedClosedAt'] >= daysPrior:
      returnIssues.append(issue)
    
  return returnIssues

def findIssue(number):
  for issue in issueList:
    if issue['number'] == number:
      return issue

def sbert(issuesTitles: list, currentTitle: str):
  mostSimilarIssueTitles = []

  model = SentenceTransformer('all-MiniLM-L6-v2')

  currentTitleEmbedding = model.encode(currentTitle)

  for similarTitle in issuesTitles:
    if currentTitle == similarTitle:
      continue
    similarTitleEmbedding = model.encode(similarTitle)
    similarity = util.pytorch_cos_sim(currentTitleEmbedding, similarTitleEmbedding)
    mostSimilarIssueTitles.append((similarTitle, similarity))

  return mostSimilarIssueTitles

def calculateSimilarities(corpus):
  currIssue = list(corpus.keys())[0]

  sb = sbert(list(corpus.keys()), currIssue)
  ordered = sorted(sb, key=lambda x: x[1], reverse=True)
  
  return ordered

for i in range(2, 19):
  issue = repo.get_issue(i)
  owner, repository, number = re.findall(regex, issue.body)[0]
  number = int(number)
  currIssue = findIssue(number)
  
  issues = [currIssue]
  issues.extend(PossibleSuggestions(currIssue))
  
  print(currIssue['number'], len(issues), len(issueList), len(PossibleSuggestions(currIssue)))
  
  corpus = {}
  # 3 sugestoes 90 dias sbert
  for i in issues:
    # 'compare': 'title + body',
    data = f"{i['title']} {i['body']}"
    
    # 'filtros.lowercase': 1,   
    data = data.lower()
    
    # 'filtros.removeLinks': 1,
    data = re.sub(r'http\S+', '', data)
    
    # 'filtros.removeDigits': 1,
    remove_digits = str.maketrans('', '', digits)
    data = data.translate(remove_digits)
    
    # 'filtros.removeStopWords': 1,
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(data)
    data = [w for w in word_tokens if not w in stop_words]
    data = ' '.join(data)
    corpus[data] = i
    
  suggestions = calculateSimilarities(corpus)
  
  comment = f'''\
To solve this issue, try looking at these suggestions:

- https://github.com/jabref/jabref/issues/{corpus[suggestions[0][0]]['number']} similarity: {(suggestions[0][1].item())*100:.2f}
- https://github.com/jabref/jabref/issues/{corpus[suggestions[1][0]]['number']} similarity: {(suggestions[1][1].item())*100:.2f}
- https://github.com/jabref/jabref/issues/{corpus[suggestions[2][0]]['number']} similarity: {(suggestions[2][1].item())*100:.2f}
'''
  issue.create_comment(comment)