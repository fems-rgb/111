import sqlite3, bcrypt
new_hash = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
conn = sqlite3.connect('zhixing.db')
cursor = conn.cursor()
cursor.execute("UPDATE users SET hashed_password=? WHERE username='admin'", (new_hash,))
conn.commit()
print(f'Password reset OK. New hash: {new_hash[:30]}...')
conn.close()
