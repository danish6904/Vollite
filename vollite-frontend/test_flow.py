import os, requests

API = 'http://127.0.0.1:5002'

def post_json(path, payload):
    r = requests.post(API + path, json=payload)
    print(path, r.status_code, r.text)
    return r

print("=== AUTH REGISTER/LOGIN ===")
r = post_json('/api/auth/register', { 'username':'demo_user', 'email':'demo@example.com', 'password':'DemoPass123' })
if r.status_code != 201:
    r = post_json('/api/auth/login', { 'username':'demo_user', 'password':'DemoPass123' })

data = r.json()
token = data.get('access_token')
print("TOKEN_PREFIX:", (token or '')[:20])

headers = {'Authorization': f'Bearer {token}'}

print("=== PROFILE ===")
r = requests.get(API + '/api/auth/profile', headers=headers)
print('/api/auth/profile', r.status_code, r.text)

print("=== UPLOAD ===")
with open('dummy.bin', 'wb') as f:
    f.write(os.urandom(2048))
files = { 'file': ('dummy.bin', open('dummy.bin', 'rb'), 'application/octet-stream') }
r = requests.post(API + '/api/analysis/upload', headers=headers, files=files)
print('/api/analysis/upload', r.status_code, r.text)

if r.status_code == 201:
    session_id = r.json().get('session_id')
    print("SESSION_ID:", session_id)

    print("=== ANALYZE ===")
    r = requests.post(API + f'/api/analysis/analyze/{session_id}', headers=headers)
    print('/api/analysis/analyze', r.status_code, r.text)

    print("=== STATUS ===")
    r = requests.get(API + f'/api/analysis/status/{session_id}', headers=headers)
    print('/api/analysis/status', r.status_code, r.text)

    print("=== RESULTS ===")
    r = requests.get(API + f'/api/analysis/results/{session_id}', headers=headers)
    print('/api/analysis/results', r.status_code, r.text)
