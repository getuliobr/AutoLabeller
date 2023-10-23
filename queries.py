import datetime
import json
import requests
from config import config

def SearchIssues(owner, name, date):
  query = f'''
    query {{
    search(query: "repo:{owner}/{name} is:issue is:closed linked:pr created:>{date} sort:created-asc", type: ISSUE, first: 100) {{
      edges {{
        node {{
          ... on Issue {{
            number
            title
            body
            createdAt
            closedAt
          }}
        }}
      }}
    }}
    rateLimit {{
      cost
    }}
  }}'''
  
  headers = {
    'Authorization': f'bearer {config["DATAMINING"]["GITHUB_TOKEN"]}',
    'Content-Type': 'application/x-www-form-urlencoded'
  }
  
  issues = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers).json()['data']['search']['edges']
  
  def parseEl(el):
    obj = el['node']
    obj['parsedCreatedAt'] = datetime.datetime.strptime(el['node']['createdAt'], '%Y-%m-%dT%H:%M:%S%z')
    obj['parsedClosedAt'] = datetime.datetime.strptime(el['node']['closedAt'], '%Y-%m-%dT%H:%M:%S%z')
    return obj
    
  
  issues = list(map(parseEl, issues))  
  
  return issues