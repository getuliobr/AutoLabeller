from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np  
import nltk

def tfidf(corpus):
  tfidf = TfidfVectorizer().fit_transform(corpus)
  pairwise_similarity = tfidf * tfidf.T

  arr = pairwise_similarity.toarray()
  np.fill_diagonal(arr, np.nan)
  return arr

def lemmatization(corpus):
  lemma = nltk.wordnet.WordNetLemmatizer()

  for i in range(len(corpus)):
    words = nltk.word_tokenize(corpus[i])
    words = [lemma.lemmatize(word) for word in words]
    corpus[i] = ' '.join(words)

  return tfidf(corpus)