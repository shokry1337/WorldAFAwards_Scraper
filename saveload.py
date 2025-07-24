import csv, os

path = 'results.csv'
headers = [
    'ID', 'Brand', 'Product', 'Producer', 'Country', 'ABV',
    'Note', 'Categories', 'Energy', 'Carbs', 'Sugars', 'Website'
]

def init():
    ids = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row and row[0].isnumeric():
                    ids.append(row[0])
        print(f"📂 Loaded '{path}'. Found {len(ids)} existing records. ")
    else:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, headers)
            writer.writeheader()
        print(f"✨ Created a fresh '{path}' with headers. ")
    return ids
        

def append(data: dict):
    try:
        with open(path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, headers)
            writer.writerow(data)
        print(f"✅ Data for ID '{data['ID']}' appended to '{path}'. ")
    except IOError as e:
        print(f"❌ Error writing data for ID '{data['ID']}' to '{path}': {e}. ")
    except csv.Error as e:
        print(f"⚠️ CSV formatting issue encountered for ID '{data['ID']}' while writing to '{path}': {e}. ")
