import pickle
from sentence_transformers import SentenceTransformer, util
from bson.binary import Binary

sbertModel = SentenceTransformer('all-MiniLM-L6-v2')

def get_sbert_embeddings(issue):
  title_body = issue["filtered"]
  
  encode = lambda x: Binary(pickle.dumps(sbertModel.encode(x)))
  
  return encode(title_body)

def sbert(issuesTitles: list, currentTitle: str, currNumber):
  mostSimilarIssueTitles = []

  currentTitleEmbedding = pickle.loads(currentTitle)

  for number, similarTitle in issuesTitles:
    if number == currNumber:
      continue

    similarTitleEmbedding = pickle.loads(similarTitle)
    similarity = util.pytorch_cos_sim(currentTitleEmbedding, similarTitleEmbedding).numpy()[0]
    similarity = float(similarity[0])
    mostSimilarIssueTitles.append((number, similarity))

  return mostSimilarIssueTitles

def getMostSimilar(currIssue, corpus):
  currIssueCompareData = corpus[currIssue]['sbert']
  corpus = [(issue_number, corpus[issue_number]['sbert']) for issue_number in corpus]

  sb = sbert(corpus, currIssueCompareData, currIssue)
  ordered = sorted(sb, key=lambda x: x[1], reverse=True)
  return ordered[0]