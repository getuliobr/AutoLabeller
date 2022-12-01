# Python program to generate word vectors using Word2Vec
# pip install nltk
# pip install gensim

# importing all necessary modules
from gensim.models import Word2Vec
import gensim
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import warnings

warnings.filterwarnings(action='ignore')


def word2vec(issues_data: list, currentTitle: str):  
  numberOfSimilarissueTitles = 5

  mostSimilarIssueTitles = []
  
  data = []

  # tokenize the sentence into words
  for issue in issues_data:
    data.append(word_tokenize(issue[4].lower()))

  CBOWModel = gensim.models.Word2Vec(
    data, min_count=1, vector_size=100, window=5)

  temp = []
  for issue in issues_data:
    _id, number, repo, owner, similarTitle = issue
    if currentTitle == similarTitle:
      continue
    similarity = CBOWModel.wv.n_similarity(word_tokenize(currentTitle.lower()), word_tokenize(similarTitle.lower()))
    mostSimilarIssueTitles.append((number, repo, owner, similarTitle, similarity))
  return mostSimilarIssueTitles