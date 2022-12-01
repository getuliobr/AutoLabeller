from sentence_transformers import SentenceTransformer, util


def sbert(issues_data: list, currentTitle: str):
  numberOfSimilarissueTitles = 5

  mostSimilarIssueTitles = []

  model = SentenceTransformer('all-MiniLM-L6-v2')

  currentTitleEmbedding = model.encode(currentTitle)

  for issue in issues_data:
    _id, number, repo, owner, similarTitle = issue
    if currentTitle == similarTitle:
      continue
    similarTitleEmbedding = model.encode(similarTitle)
    similarity = util.pytorch_cos_sim(currentTitleEmbedding, similarTitleEmbedding)
    mostSimilarIssueTitles.append((number, repo, owner, similarTitle, similarity))

  return mostSimilarIssueTitles