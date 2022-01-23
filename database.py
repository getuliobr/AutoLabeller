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
  
  def write(self, query, values):
    try:
      cur = self.db.cursor()
      cur.execute(query, values)
      self.db.commit()
      return True
    except Exception as e:
      self.db.rollback()
      return False

  def read(self, sql):
    try:
      cur = self.db.cursor()
      cur.execute(sql)
      return cur.fetchall()
    except:
      return None

