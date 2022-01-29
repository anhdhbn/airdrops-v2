from datetime import datetime, timedelta
import traceback
import json
import requests

def log(name:str, log_:str, err=False):
    current = (datetime.utcnow() + timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S')
    if err: print(f"{current} {name}: err => {log_} {traceback.format_exc()}")
    else: print(f"{current} {name}: {log_}")
    
def inputlog(name:str, log_:str):
    current = (datetime.utcnow() + timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S')
    return input(f"{current} {name}: {log_}")

def read_accounts(file_path: str = "accounts.json"):
    return json.load(open(file_path, 'r'))

def fetch_proxies():
    response = requests.get("https://proxy.webshare.io/api/proxy/list/", headers={"Authorization": "Token 67ae732e9aaec3c457c56e395e4115a7d574cd6f"})
    proxies = []
    for proxy in response.json()['results']:
        ip = proxy["proxy_address"]
        port = proxy["ports"]['socks5']
        username = proxy["username"]
        password = proxy["password"]
        proxies.append(f"socks5://{username}:{password}@{ip}:{port}")
    return proxies
