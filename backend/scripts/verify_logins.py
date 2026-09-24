import urllib.request
import urllib.error
import json

test_logins = [
    ('admin@docassistiq.com', 'AdminSecure2026!'),
    ('admin@docassistiq.com', 'admin'),
    ('admin@docassistiq.com', 'password123'),
    ('admin@hospital.org', 'AdminSecure2026!'),
    ('dr.smith@hospital.org', 'DoctorSecure2026!'),
    ('dr.smith@hospital.org', 'password123'),
    ('e2e_test5@docassistiq.com', 'DoctorSecure2026!')
]

for email, pwd in test_logins:
    req = urllib.request.Request(
        'http://localhost:8000/api/v1/auth/login',
        data=json.dumps({'email': email, 'password': pwd}).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f'SUCCESS: {email} with pwd "{pwd}" -> HTTP {resp.status}, token received!')
    except urllib.error.HTTPError as e:
        print(f'FAILED: {email} with pwd "{pwd}" -> HTTP {e.code}: {e.read().decode()[:150]}')
    except Exception as e:
        print(f'ERROR: {email} with pwd "{pwd}" -> {e}')
