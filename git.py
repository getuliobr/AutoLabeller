from github import Github, GithubIntegration
from config import config

app_id = config['GITHUB']['APP_IDENTIFIER']
app_key = config['GITHUB']['PRIVATE_KEY']

git_integration = GithubIntegration(
  app_id,
  app_key
)

def get_token(owner, repo):
  return git_integration.get_access_token(
    git_integration.get_installation(owner, repo).id
  ).token
  
def get_connection(owner, repo):
  return Github(
    login_or_token=git_integration.get_access_token(
      git_integration.get_installation(owner, repo).id
    ).token
  )