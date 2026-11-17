"""Fetch a small number of test rows from the public LOTUSDIS dataset."""
import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--count', type=int, default=5)
    p.add_argument('--out', type=Path, default=Path('lotusdis'))
    args = p.parse_args()
    if not 1 <= args.count <= 20:
        p.error('count must be between 1 and 20')
    args.out.mkdir(parents=True, exist_ok=True)
    query = urllib.parse.urlencode({'dataset': 'nectec/LOTUSDIS', 'config': 'default', 'split': 'test', 'offset': 0, 'length': args.count})
    with urllib.request.urlopen('https://datasets-server.huggingface.co/rows?' + query, timeout=60) as resp:
        data = json.load(resp)
    rows = []
    for sample in data['rows']:
        row = sample['row']
        if not row.get('sentence') or not row.get('audio'):
            continue
        name = f"row-{sample['row_idx']:03d}.wav"
        with urllib.request.urlopen(row['audio'][0]['src'], timeout=60) as resp:
            (args.out / name).write_bytes(resp.read())
        rows.append({'audio': name, 'reference': row['sentence'], 'row_idx': sample['row_idx'], 'speaker_id': row.get('speaker_id'), 'mic': row.get('mic'), 'duration': row.get('duration')})
    if not rows:
        raise ValueError('no rows with both audio and reference')
    (args.out / 'manifest.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Downloaded {len(rows)} samples to {args.out}')


if __name__ == '__main__':
    main()
