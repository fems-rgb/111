import sqlite3
conn = sqlite3.connect('zhixing.db')
cursor = conn.cursor()
cursor.execute("SELECT hashed_password FROM users WHERE username='admin'")
pwd = cursor.fetchone()[0]
print('Current hash:', pwd[:80])
if pwd.startswith('$') or pwd.startswith('$'):
    print('Hash type: bcrypt')
elif len(pwd) == 64:
    print('Hash type: sha256')
else:
    print(f'Hash type: other, length={len(pwd)}')
conn.close()
