import urllib.request, time, json

for ep in ['/health', '/ready', '/api/v1/ping']:
    t0 = time.time()
    try:
        req = urllib.request.Request(f'http://localhost:8000{ep}')
        with urllib.request.urlopen(req, timeout=10) as r:
            code = r.status
            body = r.read().decode()
            dt = time.time() - t0
            print(f'{ep} -> code={code} in {dt:.3f}s: {body[:120]}')
    except urllib.error.HTTPError as e:
        dt = time.time() - t0
        body = e.read().decode()
        print(f'{ep} -> HTTPError code={e.code} in {dt:.3f}s: {body[:120]}')
    except Exception as e:
        dt = time.time() - t0
        print(f'{ep} -> Error: {e} in {dt:.3f}s')
