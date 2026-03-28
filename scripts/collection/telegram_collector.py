#!/usr/bin/env python3
"""
Telegram Channel Collector — CR-AI Project v2
All channel usernames verified as working.

First run: phone verification required once.
After that: runs silently via cron.

Run: python3 scripts/collection/telegram_collector.py
"""

from dotenv import load_dotenv
load_dotenv('/Users/omarnabi/Desktop/CR-AI/.env')

import os, asyncio, json, logging, hashlib
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/Users/omarnabi/Desktop/CR-AI/logs/telegram.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

API_ID   = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
OUT_DIR  = Path('/Users/omarnabi/Desktop/CR-AI/data/raw/social_media')
OUT_DIR.mkdir(parents=True, exist_ok=True)
SESSION  = '/Users/omarnabi/Desktop/CR-AI/logs/cr_ai_telegram'

# ─── Verified channels ────────────────────────────────────────────────────────
# All usernames confirmed working as of 2026-03-25

CHANNELS = [
    # Iran / Hormuz — English
    {'username': 'IranIntl_En',   'perspective': 'Iranian-opposition-exile',  'lang': 'en', 'pilot': 'iran_hormuz'},
    {'username': 'PressTV',        'perspective': 'Iranian-state',              'lang': 'en', 'pilot': 'iran_hormuz'},

    # Iran / Hormuz — Persian (Farsi) — translation_required: True
    {'username': 'bbcpersian',     'perspective': 'Western-Persian-diaspora',   'lang': 'fa', 'pilot': 'iran_hormuz'},
    {'username': 'khamenei_ir',    'perspective': 'Iranian-supreme-leader',     'lang': 'fa', 'pilot': 'iran_hormuz'},

    # Afghanistan — Dari/Persian — translation_required: True
    {'username': 'Tolo_News',      'perspective': 'Afghan-independent',         'lang': 'fa', 'pilot': 'afghanistan'},
]

# ─── Collector ────────────────────────────────────────────────────────────────

async def collect(limit=500):
    async with TelegramClient(SESSION, API_ID, API_HASH) as client:
        log.info('Connected to Telegram')
        total = 0
        for ch in CHANNELS:
            log.info(f'Collecting @{ch["username"]} ({limit} messages)...')
            out_path = OUT_DIR / f'telegram_{ch["username"]}.jsonl'
            count = 0
            try:
                async for msg in client.iter_messages(ch['username'], limit=limit):
                    if not msg.text or len(msg.text) < 20:
                        continue
                    rec = {
                        'id': hashlib.sha256(
                            f'{ch["username"]}{msg.id}'.encode()
                        ).hexdigest()[:16],
                        'platform': 'telegram',
                        'channel': ch['username'],
                        'source_name': f'Telegram @{ch["username"]}',
                        'source_perspective': ch['perspective'],
                        'language': ch['lang'],
                        'date': msg.date.isoformat(),
                        'text': msg.text,
                        'views': msg.views or 0,
                        'category': 'social_media',
                        'pilot_conflicts': [ch['pilot']],
                        'conflict_types': [],
                        'translation_required': ch['lang'] != 'en',
                        'collected_at': datetime.utcnow().isoformat()
                    }
                    with open(out_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
                    count += 1
                log.info(f'  -> {count} messages saved from @{ch["username"]}')
                total += count
            except Exception as e:
                log.error(f'  -> Failed @{ch["username"]}: {e}')
        log.info(f'Telegram collection complete: {total} total messages')
        return total

if __name__ == '__main__':
    asyncio.run(collect())
