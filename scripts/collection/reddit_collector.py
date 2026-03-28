#!/usr/bin/env python3
"""
Reddit Collector — CR-AI
Uses Pushshift dumps mirrored on Internet Archive.
Zero credentials required — fully anonymous, no API key, no account.

Strategy:
  1. Pull monthly .zst dump files from Internet Archive (pushshift mirror)
  2. Stream-decompress and filter for relevant subreddits
  3. Fall back to Reddit's public JSON API (no auth, ~25 posts/sub)

Install: pip install zstandard requests
"""

import json, hashlib, logging, requests, io
from datetime import datetime, timezone
from pathlib import Path

try:
    import zstandard as zstd
    HAS_ZST = True
except ImportError:
    HAS_ZST = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(Path(__file__).parent.parent.parent / "logs" / "reddit.log")),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

OUT_DIR = Path(__file__).parent.parent.parent / "data" / "raw" / "social_media"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SUBREDDITS = [
    {"sub": "iran",          "pilot": "iran_hormuz",  "perspective": "Iranian-diaspora-English"},
    {"sub": "iranian",       "pilot": "iran_hormuz",  "perspective": "Iranian-diaspora-English"},
    {"sub": "MiddleEast",    "pilot": "iran_hormuz",  "perspective": "MENA-perspective"},
    {"sub": "afghanistan",   "pilot": "afghanistan",  "perspective": "Afghan-diaspora-English"},
    {"sub": "afghanistan2",  "pilot": "afghanistan",  "perspective": "Afghan-diaspora-English"},
    {"sub": "geopolitics",   "pilot": "both",         "perspective": "International-analysis"},
    {"sub": "worldnews",     "pilot": "both",         "perspective": "Western-English-news"},
    {"sub": "worldpolitics", "pilot": "both",         "perspective": "Western-English-politics"},
]

TARGET_SUBS = {cfg["sub"].lower() for cfg in SUBREDDITS}

# Pushshift monthly submission dumps (original host)
# Format: https://files.pushshift.io/reddit/submissions/RS_YYYY-MM.zst
# Note: if unavailable, the public JSON fallback always runs instead
PUSHSHIFT_BASE = "https://files.pushshift.io/reddit/submissions"

def _sub_to_pilots(sub):
    sub = sub.lower()
    for cfg in SUBREDDITS:
        if cfg["sub"].lower() == sub:
            pilots = ["iran_hormuz", "afghanistan"] if cfg["pilot"] == "both" else [cfg["pilot"]]
            return pilots, cfg["perspective"]
    return ["both"], "Unknown"

def make_record(post, sub):
    pilots, perspective = _sub_to_pilots(sub)
    text = f"{post.get('title', '')}. {post.get('selftext', '')}".strip()
    uid = hashlib.sha256(post.get("id", text[:40]).encode()).hexdigest()[:16]
    ts = post.get("created_utc", 0)
    date = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else datetime.utcnow().isoformat()
    return {
        "id": uid,
        "platform": "reddit",
        "subreddit": sub,
        "source_name": f"r/{sub}",
        "source_url": f"https://reddit.com/r/{sub}/comments/{post.get('id', '')}",
        "source_country": "Multiple",
        "source_perspective": perspective,
        "date": date,
        "language": "en",
        "category": "social_media",
        "pilot_conflicts": pilots,
        "conflict_types": [],
        "text": text[:3000],
        "score": post.get("score", 0),
        "num_comments": post.get("num_comments", 0),
        "translation_required": False,
        "confidence": "medium",
        "notes": "Reddit via Pushshift/IA archive or public JSON",
        "collected_at": datetime.utcnow().isoformat()
    }

def collect_via_public_json(cfg, limit=100):
    """
    Fallback: Reddit public JSON endpoint — no auth, ~25-100 posts.
    Works without any credentials.
    """
    sub = cfg["sub"]
    log.info(f"  [public JSON] r/{sub}")
    headers = {"User-Agent": "CR-AI-Collector/3.0 (research; contact: research@example.com)"}
    count = 0
    out_path = OUT_DIR / f"reddit_{sub}.jsonl"
    seen = set()

    for sort in ("hot", "top"):
        url = f"https://www.reddit.com/r/{sub}/{sort}.json?limit=100&t=month"
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                log.warning(f"    r/{sub} {sort}: HTTP {resp.status_code}")
                continue
            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            for child in posts:
                post = child.get("data", {})
                pid = post.get("id", "")
                if pid in seen or len(post.get("title", "")) < 5:
                    continue
                seen.add(pid)
                rec = make_record(post, sub)
                if len(rec["text"]) < 20:
                    continue
                with open(out_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count += 1
        except Exception as e:
            log.error(f"    r/{sub} {sort}: {e}")

    log.info(f"  r/{sub}: {count} posts (public JSON)")
    return count


def collect_via_pushshift_ia(year_month="2024-01", max_per_sub=500):
    """
    Stream Pushshift monthly dump from Internet Archive.
    Filters for our target subreddits only — never downloads full file.
    year_month: e.g. '2024-01'
    """
    if not HAS_ZST:
        log.warning("zstandard not installed — skipping Pushshift stream. pip install zstandard")
        return 0

    url = f"{PUSHSHIFT_BASE}/RS_{year_month}.zst"
    log.info(f"Streaming Pushshift dump: {url}")

    counts = {sub: 0 for sub in TARGET_SUBS}
    out_handles = {}

    try:
        resp = requests.get(url, stream=True, timeout=30)
        if resp.status_code != 200:
            log.warning(f"Pushshift IA returned {resp.status_code} for {year_month}")
            return 0

        dctx = zstd.ZstdDecompressor()
        reader = dctx.stream_reader(resp.raw)
        text_stream = io.TextIOWrapper(reader, encoding="utf-8", errors="replace")

        for line in text_stream:
            line = line.strip()
            if not line:
                continue
            try:
                post = json.loads(line)
            except json.JSONDecodeError:
                continue

            sub = post.get("subreddit", "").lower()
            if sub not in TARGET_SUBS:
                continue
            if counts[sub] >= max_per_sub:
                if all(v >= max_per_sub for v in counts.values()):
                    break
                continue

            rec = make_record(post, sub)
            if len(rec["text"]) < 20:
                continue

            if sub not in out_handles:
                out_handles[sub] = open(OUT_DIR / f"reddit_{sub}.jsonl", "a", encoding="utf-8")
            out_handles[sub].write(json.dumps(rec, ensure_ascii=False) + "\n")
            counts[sub] += 1

    except Exception as e:
        log.error(f"Pushshift stream error: {e}")
    finally:
        for fh in out_handles.values():
            fh.close()

    total = sum(counts.values())
    log.info(f"Pushshift stream complete: {total} records across {len([v for v in counts.values() if v > 0])} subs")
    for sub, n in counts.items():
        if n > 0:
            log.info(f"  r/{sub}: {n}")
    return total

def run_reddit_collection():
    """
    Main entry point.
    1. Try Pushshift IA stream for last 3 months (rich historical data)
    2. Always run public JSON fallback for fresh recent posts
    """
    from datetime import date

    total = 0

    # Step 1: Pushshift stream — last 3 months
    if HAS_ZST:
        today = date.today()
        for delta in range(1, 4):  # 1, 2, 3 months back
            month = today.month - delta
            year = today.year
            if month <= 0:
                month += 12
                year -= 1
            ym = f"{year}-{month:02d}"
            total += collect_via_pushshift_ia(year_month=ym, max_per_sub=300)
    else:
        log.info("zstandard not available — skipping Pushshift stream")

    # Step 2: Public JSON fallback — always runs, gets latest posts
    log.info("Running public JSON fallback for fresh posts...")
    for cfg in SUBREDDITS:
        total += collect_via_public_json(cfg)

    log.info(f"Reddit collection complete: {total} total records")
    return total


if __name__ == "__main__":
    run_reddit_collection()
