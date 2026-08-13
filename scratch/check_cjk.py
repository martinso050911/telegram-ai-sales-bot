import os
import sqlite3

def is_cjk(char):
    code = ord(char)
    return (0x4E00 <= code <= 0x9FFF) or (0x3400 <= code <= 0x4DBF) or (0x20000 <= code <= 0x2A6DF)

print("--- AUDITING SOURCE FILES ---")
for root, dirs, files in os.walk('.'):
    if any(p in root for p in ['venv', '.git', '__pycache__']):
        continue
    for file in files:
        if file.endswith(('.py', '.html', '.css', '.js', '.md')):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        if '客户' in line or any(is_cjk(c) for c in line):
                            print(f"[FILE] {filepath}:{i} -> {line.strip()}")
            except Exception as e:
                pass

print("--- AUDITING SQLITE DATABASE ---")
if os.path.exists('sales_b2b.db'):
    conn = sqlite3.connect('sales_b2b.db')
    cursor = conn.cursor()
    tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    for table in tables:
        rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
        for row in rows:
            row_str = str(row)
            if '客户' in row_str or any(is_cjk(c) for c in row_str):
                print(f"[DB] Table '{table}': {row_str}")

print("--- AUDIT COMPLETE ---")
