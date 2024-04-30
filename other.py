import sqlite3
from datetime import datetime

conn = sqlite3.connect('record.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS updates (
                    update_id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    menu_item_name TEXT,
                    overall_cost REAL,
                    quantity INTEGER
                )''')
conn.commit()
conn.close()

