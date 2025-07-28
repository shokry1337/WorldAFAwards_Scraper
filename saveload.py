import csv, os
from datetime import datetime

def log(*args, **kw):
    print(f"{datetime.now().strftime('[%I:%M:%S %p]')}", *args, **kw)

path = 'results.csv'
headers = [
    'ID', 'Brand', 'Product', 'Producer', 'Country', 'ABV',
    'Note', 'Categories', 'Energy', 'Carbs', 'Sugars', 'Website'
]

def init():
    ids = []
    if os.path.exists(path):
        if os.path.getsize(path) == 0:
            with open(path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, headers)
                writer.writeheader()
        else:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if row and row[0].isnumeric():
                        ids.append(row[0])
        log(f"📂 Found {len(ids)} records in '{path}'.")
    else:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, headers)
            writer.writeheader()
        log(f"✨ Created '{path}'.")
    return ids

def append(data: dict):
    try:
        with open(path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, headers)
            writer.writerow(data)
        log(f"✅ ID {data['ID']} saved.")
    except IOError as e:
        log(f"❌ Write error for ID {data['ID']}: {e}")
    except csv.Error as e:
        log(f"⚠️ CSV error for ID {data['ID']}: {e}")