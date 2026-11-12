"""menplus Customer Insights - read-only Reddit reader.

Reads public posts and comments from a short list of subreddits and saves
the text to a local JSONL file for internal product research.

Read-only: this script never posts, comments, votes or sends messages.

Setup (script-type app from https://www.reddit.com/prefs/apps):
    set REDDIT_CLIENT_ID=...
    set REDDIT_CLIENT_SECRET=...
    set REDDIT_USERNAME=...
    set REDDIT_PASSWORD=...
    python reddit_reader.py
"""
import base64
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SUBREDDITS = ["malefashionadvice", "bigmenfashion", "tall", "BigAndTall", "frugalmalefashion"]
POSTS_PER_SUB = 25          # newest posts per subreddit per run
COMMENTS_PER_POST = 50
DELAY_SECONDS = 2.0         # ~30 requests/minute, far below Reddit's limit
USER_AGENT = "script:menplus-customer-insights:v1.0 (read-only research)"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def get_token():
    auth = base64.b64encode(
        f"{os.environ['REDDIT_CLIENT_ID']}:{os.environ['REDDIT_CLIENT_SECRET']}".encode()).decode()
    body = urllib.parse.urlencode({
        "grant_type": "password",
        "username": os.environ["REDDIT_USERNAME"],
        "password": os.environ["REDDIT_PASSWORD"],
        "scope": "read",            # read scope only
    }).encode()
    req = urllib.request.Request("https://www.reddit.com/api/v1/access_token", data=body,
                                 headers={"Authorization": f"Basic {auth}", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["access_token"]


def get(token, path, **params):
    url = "https://oauth.reddit.com" + path + "?" + urllib.parse.urlencode({**params, "raw_json": 1})
    req = urllib.request.Request(url, headers={"Authorization": f"bearer {token}", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    time.sleep(DELAY_SECONDS)
    return data


def walk_comments(children, out):
    for c in children:
        if c.get("kind") != "t1":
            continue
        d = c["data"]
        if d.get("body") and d["body"] not in ("[deleted]", "[removed]"):
            out.append({"id": d["id"], "body": d["body"], "score": d.get("score")})
        replies = d.get("replies")
        if isinstance(replies, dict):
            walk_comments(replies["data"]["children"], out)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    token = get_token()
    out_path = os.path.join(OUT_DIR, datetime.now(timezone.utc).strftime("%Y%m%d") + ".jsonl")
    with open(out_path, "a", encoding="utf-8") as f:
        for sub in SUBREDDITS:
            listing = get(token, f"/r/{sub}/new", limit=POSTS_PER_SUB)
            for child in listing["data"]["children"]:
                p = child["data"]
                thread = get(token, f"/comments/{p['id']}", limit=COMMENTS_PER_POST, depth=3)
                comments = []
                walk_comments(thread[1]["data"]["children"], comments)
                # No usernames are stored: only post/comment text for research.
                f.write(json.dumps({
                    "subreddit": sub,
                    "id": p["id"],
                    "title": p.get("title"),
                    "text": p.get("selftext"),
                    "score": p.get("score"),
                    "created_utc": p.get("created_utc"),
                    "comments": comments,
                }, ensure_ascii=False) + "\n")
            print(f"r/{sub}: {len(listing['data']['children'])} posts")
    print("saved", out_path)


def delete_ids(ids):
    """Remove posts/comments by id from all saved files (used for deletion requests within 48h)."""
    ids = set(ids)
    for name in os.listdir(OUT_DIR):
        path = os.path.join(OUT_DIR, name)
        rows = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                if row["id"] in ids:
                    continue
                row["comments"] = [c for c in row["comments"] if c["id"] not in ids]
                rows.append(row)
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


if __name__ == "__main__":
    main()
