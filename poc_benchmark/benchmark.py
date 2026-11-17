"""Small reproducible ASR comparison; see README.md for scope and limitations."""
import argparse
import hashlib
import importlib.metadata
import json
import time
import unicodedata
from pathlib import Path


def normalized(text):
    text = unicodedata.normalize('NFC', text).casefold()
    return ''.join(c for c in text if not c.isspace() and not unicodedata.category(c).startswith('P'))


def distance(a, b):
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        previous, row[0] = row[0], i
        for j, y in enumerate(b, 1):
            old = row[j]
            row[j] = min(row[j] + 1, row[j-1] + 1, previous + (x != y))
            previous = old
    return row[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', type=Path, required=True, help='JSON list with audio and reference fields')
    ap.add_argument('--models', nargs='+', default=['tiny', 'large-v3-turbo'])
    ap.add_argument('--device', default='cpu', choices=['cpu', 'cuda'])
    ap.add_argument('--out', type=Path, default=Path('benchmark-results.json'))
    args = ap.parse_args()
    import torch
    import whisper
    samples = json.loads(args.manifest.read_text(encoding='utf-8'))
    if not samples:
        raise ValueError('manifest is empty')
    report = {'method': 'NFC + casefold; remove whitespace and Unicode punctuation; corpus CER=sum edit distances/sum reference characters',
              'limitations': 'Small smoke test; not representative of LINE, overlapping speakers, or code-switching.',
              'whisper_version': importlib.metadata.version('openai-whisper'), 'torch_version': torch.__version__,
              'device_requested': args.device, 'cuda_available': torch.cuda.is_available(), 'models': []}
    for name in args.models:
        result = {'name': name, 'device': args.device, 'decoding': {'language': 'th', 'task': 'transcribe', 'fp16': args.device == 'cuda'}, 'samples': []}
        if name in whisper._MODELS:
            result['model_url'] = whisper._MODELS[name]
            result['model_sha256'] = whisper._MODELS[name].split('/')[-2]
        report['models'].append(result)
        try:
            start = time.perf_counter()
            model = whisper.load_model(name, device=args.device)
            result['model_load_seconds'] = round(time.perf_counter() - start, 3)
            totals = [0, 0]
            for item in samples:
                wav = (args.manifest.parent / item['audio']).resolve()
                reference = item['reference']
                nref = normalized(reference)
                if not nref:
                    raise ValueError('empty normalized reference')
                start = time.perf_counter()
                output = model.transcribe(str(wav), language='th', task='transcribe', fp16=args.device == 'cuda')
                elapsed = time.perf_counter() - start
                hyp = output['text'].strip()
                errors = distance(nref, normalized(hyp))
                totals[0] += errors
                totals[1] += len(nref)
                result['samples'].append({'audio': item['audio'], 'sha256': hashlib.sha256(wav.read_bytes()).hexdigest(), 'reference': reference, 'hypothesis': hyp, 'edits': errors, 'reference_chars': len(nref), 'cer': errors / len(nref), 'seconds': round(elapsed, 3)})
                result['status'] = 'running'
                args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            result['corpus_cer'] = totals[0] / totals[1]
            result['status'] = 'ok'
            del model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception as exc:
            result['status'] = 'error'
            result['error'] = f'{type(exc).__name__}: {exc}'
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
