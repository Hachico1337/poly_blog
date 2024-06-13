import sqlite3

db_path = 'users.db'

conn = sqlite3.connect(db_path)

cursor = conn.cursor()

cursor.execute("DELETE FROM alembic_version;")

conn.commit()

conn.close()