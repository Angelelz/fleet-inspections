import sqlite3, datetime
from helpers import as_dict
from large_tables import c1

db_path = "./fleets.db"
db = sqlite3.connect(db_path)
db.row_factory = sqlite3.Row
inspections = dict(db.execute("SELECT * FROM inspections WHERE c_id = ? AND v_id = ? ORDER BY date DESC",
                                            [1, 2]).fetchone())
db.close()
#db.commit()
inspection = [[inspections[c[1]], c[3]]  for c in c1 if inspections[c[0]] == 0]
print(inspection)