from database import Connection

db = Connection()

sql = f"select title from issues where title is not null"
issues_data = db.read(sql)

with open('titles.txt', 'w+', encoding="utf-8") as f:
  for titles in issues_data:
    
    f.write(f"{titles[0]}\n")

