import shutil

targets = ['scraper', 'saveload']
for target in targets:
    try:
        shutil.copy(target + '.py', target + '.bak')
    except Exception as e:
        print(f'{target} - {e} - ❌')
    else:
        print(f'{target} - ✔️')