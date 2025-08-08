import sqlite3

# Create or connect to database
conn = sqlite3.connect('activity.db')
c = conn.cursor()

# Create a table to store activity time (if not exists)
c.execute('''
CREATE TABLE IF NOT EXISTS activity_log (
    user_id TEXT,
    username TEXT,
    last_seen TIMESTAMP,
    total_seconds INTEGER DEFAULT 0
)
''')

conn.commit()
conn.close()