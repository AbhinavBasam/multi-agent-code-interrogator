import urllib.request, json
url = 'https://api.github.com/users/AbhinavBasam/repos?per_page=100'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        repos = json.loads(response.read().decode())
        for r in repos:
            print(f"Repo: {r['name']}, Language: {r['language']}")
except Exception as e:
    print('Error:', e)
