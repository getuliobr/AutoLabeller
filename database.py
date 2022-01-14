import psycopg2
from config import config

class Connection():
  def __init__(self):
    self.db = psycopg2.connect(
      host=config['DATABASE']['HOST'],
      database=config['DATABASE']['DB'],
      user=config['DATABASE']['USER'],
      password=config['DATABASE']['PASSWORD']
    )
  
  def query(self, query):
    try:
      cur = self.db.cursor()
      cur.execute(query)
      result = True
      if 'SELECT' in query:
        result = cur.fetchall()
      cur.close()
      self.db.commit()
      return result
    except Exception as e:
      print(e)
      return False