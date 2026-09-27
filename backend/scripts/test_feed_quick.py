import urllib.request
import json

def test():
    # 1. Login
    login_data = json.dumps({'email': 'dr.smith@hospital.org', 'password': 'DoctorSecure2026!'}).encode()
    login_req = urllib.request.Request('http://127.0.0.1:8001/api/v1/auth/login', data=login_data, headers={'Content-Type': 'application/json'})
    token = json.loads(urllib.request.urlopen(login_req).read().decode())['access_token']
    print("Token obtained successfully.")

    # 2. Feed via Next.js
    feed_req = urllib.request.Request('http://localhost:3000/api/v1/hub/feed', headers={'Authorization': f'Bearer {token}'})
    res = urllib.request.urlopen(feed_req)
    posts = json.loads(res.read().decode())
    print(f"Proxied through Next.js successfully! Total posts: {len(posts)}")
    for p in posts[:2]:
        print(f"Post: {p['disease_name']} by {p.get('author_name')} ({p.get('author_specialty')})")

if __name__ == '__main__':
    test()
