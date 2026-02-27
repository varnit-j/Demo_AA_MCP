import sqlite3, os
base = r'D:\varnit\demo\2101_f\2101_UI_Chang\dummy\AA_Flight_booking_2402\AA_Flight_booking_2302'
dbs = [
    'db.sqlite3',
    'microservices/backend-service/db.sqlite3',
    'microservices/loyalty-service/db.sqlite3',
    'microservices/payment-service/db.sqlite3',
    'microservices/ui-service/db.sqlite3',
]
for db in dbs:
    p = os.path.join(base, db.replace('/', os.sep))
    c = sqlite3.connect(p)
    rows = c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    print(f'=== {db} ===')
    for r in rows:
        count = c.execute(f'SELECT COUNT(*) FROM "{r[0]}"').fetchone()[0]
        print(f'  {r[0]}  ({count} rows)')
    c.close()
