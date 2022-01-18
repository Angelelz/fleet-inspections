import sqlite3
from helpers import as_dict

db_path = "./fleets.db"
db = sqlite3.connect(db_path)
db.row_factory = sqlite3.Row
tup = db.execute("SELECT date FROM inspections ORDER BY date DESC").fetchone()
print(tup["date"])
#db.commit()
db.close()