import urllib.request, re

req = urllib.request.Request('https://unmtid-dbs.net/download/', headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        html = r.read().decode('utf-8', errors='ignore')
        links = re.findall(r'href=["\']([^"\']+)["\']', html)
        for l in links:
            if any(ext in l.lower() for ext in ['.tsv', '.csv', '.sql', '.gz', '.zip', '.pgdump']):
                print('Found link:', l)
except Exception as e:
    print('Error:', e)
