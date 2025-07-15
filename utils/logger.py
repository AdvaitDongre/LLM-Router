import os
import json
import csv
from threading import Lock

LOG_DIR = 'logs'
JSON_LOG = os.path.join(LOG_DIR, 'prompts.json')
CSV_LOG = os.path.join(LOG_DIR, 'prompts.csv')

log_lock = Lock()

def log_interaction(timestamp, prompt, model, response, latency, token_count, prompt_id, from_cache=False):
    entry = {
        'timestamp': timestamp,
        'prompt': prompt,
        'model': model,
        'response': response,
        'latency_ms': latency,
        'token_count': token_count,
        'prompt_id': prompt_id,
        'rating': None,
        'from_cache': from_cache
    }
    with log_lock:
        # JSON log
        if os.path.exists(JSON_LOG):
            with open(JSON_LOG, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = []
        data.append(entry)
        with open(JSON_LOG, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # CSV log
        write_header = not os.path.exists(CSV_LOG)
        with open(CSV_LOG, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=entry.keys())
            if write_header:
                writer.writeheader()
            writer.writerow(entry)

def log_rating(prompt_id, score, timestamp):
    with log_lock:
        # Update JSON log
        if os.path.exists(JSON_LOG):
            with open(JSON_LOG, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = []
        for entry in data:
            if entry['prompt_id'] == prompt_id:
                entry['rating'] = score
                entry['rating_timestamp'] = timestamp
        with open(JSON_LOG, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # Update CSV log
        if os.path.exists(CSV_LOG):
            rows = []
            with open(CSV_LOG, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['prompt_id'] == prompt_id:
                        row['rating'] = score
                        row['rating_timestamp'] = timestamp
                    rows.append(row)
            with open(CSV_LOG, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

def get_prompt_id(timestamp, prompt, model):
    import hashlib
    base = f'{timestamp}:{prompt}:{model}'
    return hashlib.sha256(base.encode()).hexdigest()[:16] 