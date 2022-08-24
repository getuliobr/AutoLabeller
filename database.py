import psycopg2
from config import config

class Connection():
  def __init__(self):
    self.db = psycopg2.connect(
      host=config['DATABASE']['HOST'],
      port=config['DATABASE']['PORT'],
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
      print(e)
      self.db.rollback()
      return False

  def read(self, sql, values = None):
    try:
      cur = self.db.cursor()
      if values:
        cur.execute(sql, values)
      else:
        cur.execute(sql)
      return cur.fetchall()
    except:
      return None

