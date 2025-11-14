import psycopg2

def load_env():
    env = {}
    with open('config/.env', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                env[key.strip()] = val.strip()  # <- STRIP hinzugefügt!
    return env

env = load_env()
conn = psycopg2.connect(
    host=env['LOCOSOFT_HOST'], 
    port=int(env['LOCOSOFT_PORT']),
    database=env['LOCOSOFT_DATABASE'], 
    user=env['LOCOSOFT_USER'],
    password=env['LOCOSOFT_PASSWORD']
)
cur = conn.cursor()

print("=== VEHICLES SCHEMA ===")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns
    WHERE table_name = 'vehicles'
    ORDER BY ordinal_position
    LIMIT 20;
""")
for col, dtype in cur.fetchall():
    print(f"  {col:<30} {dtype}")

print("\n=== JOIN-MÖGLICHKEITEN ===")
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns
    WHERE table_name = 'vehicles'
      AND (column_name LIKE '%number%' OR column_name = 'vin')
""")
for col in cur.fetchall():
    print(f"  - {col[0]}")

conn.close()
