import requests, time
from config import config
from git import get_token

from compareAlgorithms.filtered import get_filtered
from compareAlgorithms.sbert import get_sbert_embeddings

def query(q, owner, repo):
  return requests.post(
    'https://api.github.com/graphql',
    json = {'query': q},
    headers={
      'Authorization': f'bearer {config["GITHUB"]["TOKEN"] if not owner or not repo else get_token(owner, repo)}'
    }
  ).json()

def get_closed_issue_with_linked_pr(owner, repo, date='2000-01-01T00:00:00Z', first = 49, orderBy='created'):
  buildQuery = lambda date: f'''
  query {{
    search(query: "repo:{owner}/{repo} is:issue state:closed linked:pr {orderBy}:>{date} sort:{orderBy}-asc", type: ISSUE, first: {first}) {{
    edges {{
      node {{
      ... on Issue {{
        number
        state
        title
        body
        labels(first: 100) {{
          nodes {{
            name
          }}
        }}
        closedAt
        createdAt
        timelineItems(first: 100) {{
          nodes {{
            ... on ClosedEvent {{
              stateReason
              closer {{
                ... on PullRequest {{
                  number
                  title
                  state
                  createdAt
                  closedAt
                  mergedAt
                  files(first: 100) {{
                    nodes {{
                    ... on PullRequestChangedFile {{
                      path
                    }}
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
      }}
      }}
    }}
    }}
    rateLimit {{
      cost
      remaining
      resetAt
    }}
  }}'''
  # print(q)
  result = query(buildQuery(date), owner, repo)
  try:
    if "errors" in result and len(result['errors']):
      print("Got error:", result['errors'] )
      print("Waiting 10s trying to fix")
      time.sleep(10)
      return get_closed_issue_with_linked_pr(owner, repo, date, first)
    return result['data']['search']['edges']
  except Exception as e:
    print("err:", result)
    raise e

def clean_up(setLowercase=True, removeLinks=True, removeDigits=True, removeStopWords=True):
  def wrapped(issue):
    issue = issue["node"]
    issue["labels"] = [ node["name"] for node in issue["labels"]["nodes"] if node ]
    
    linkedPrs = [ node["closer"] for node in issue["timelineItems"]["nodes"] if node and node["stateReason"] == "COMPLETED" and node["closer"]]
    files = []
    
    for pr in linkedPrs:
      if not pr["files"]:
        continue
      prFiles = pr["files"]["nodes"] 
      for file in prFiles:
        if file:
          files.append(file["path"])
    
    issue["files"] = list(set(files))
    
    issue["prs"] = list(set([ pr["number"] for pr in linkedPrs ]))
    issue["closed_at"] = issue["closedAt"]
    issue["created_at"] = issue["createdAt"]
  
    issue["lowercase"] = setLowercase
    issue["removeLinks"] = removeLinks
    issue["removeDigits"] = removeDigits
    issue["removeStopWords"] = removeStopWords
    issue["filtered"] = get_filtered(issue)
    issue["sbert"] = get_sbert_embeddings(issue)
        
    del issue["timelineItems"], issue["closedAt"], issue["createdAt"], issue["state"]
    return issue
  return wrapped

def get_issues(owner, repo, date='2000-01-01T00:00:00Z', setLowercase=True, removeLinks=True, removeDigits=True, removeStopWords=True):
  issues = []
  lastFetch = -1
  while lastFetch:
    date = date if not len(issues) else issues[-1]['node']['createdAt']
    print(date, len(issues))
    issueList = get_closed_issue_with_linked_pr(owner, repo, date)
    issues.extend(issueList)
    lastFetch = len(issueList)
  return list(map(clean_up(setLowercase, removeLinks, removeDigits, removeStopWords), issues))

def get_issue_by_closed(owner, repo, closed_at):
  issue = get_closed_issue_with_linked_pr(owner, repo, closed_at, orderBy='closed')
  return list(map(clean_up(), issue))