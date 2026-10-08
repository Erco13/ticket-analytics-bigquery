import os, time
import requests

API = "https://api.github.com"

def make_session():
    s = requests.Session()
    s.headers.update({
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "X-GitHub-Api-Version": "2026-03-10",
    })
    return s

def get_with_retry(session, url, params=None, max_retries=5):
    for attempt in range(max_retries):
        try:
            r = session.get(url, params=params, timeout=30)
        except (requests.ConnectionError, requests.Timeout):
            time.sleep(2 ** attempt)  # cădere scurtă de rețea: așteaptă și reîncearcă
            continue
        if r.status_code in (403, 429):
            if "retry-after" in r.headers:
                wait = int(r.headers["retry-after"])
            elif r.headers.get("x-ratelimit-remaining") == "0":
                wait = int(r.headers["x-ratelimit-reset"]) - int(time.time()) + 1
            else:
                wait = 60
            time.sleep(max(wait, 1))
            continue
        if r.status_code >= 500:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        return r
    raise RuntimeError(f"Eșec după {max_retries} încercări: {url}")

def fetch_issues(session, repo, since_iso):
    url = f"{API}/repos/{repo}/issues"
    params = {"state": "all", "sort": "updated", "direction": "asc",
              "since": since_iso, "per_page": 100}
    while url:
        r = get_with_retry(session, url, params)
        yield from r.json()
        url = r.links.get("next", {}).get("url")
        params = None  # linkul next conține deja parametrii