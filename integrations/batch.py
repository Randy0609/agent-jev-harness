"""Preserve every record while using SemDecide's real filter_records API."""
import math
import sys
from integrations.kit import source

sys.path.insert(0, str(source('semdecide') / 'src'))
from reflex_guard.commands import filter_records


def screen(records, provider, criterion, threshold=0.8, margin=0.1):
    if not 0 <= threshold - margin < threshold + margin <= 1:
        raise ValueError('Invalid thresholds')
    if not 1 <= len(records) <= 100:
        raise ValueError('Use batches of 1–100 records')
    ids = [r.get('id') for r in records]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('Every record must have a unique string id')
    if any(not isinstance(r.get('text'), str) or len(r['text']) > 2000 for r in records):
        raise ValueError('Each text must be a string of at most 2000 characters')
    if sum(len(r['text'].encode()) for r in records) > 20000:
        raise ValueError('Batch exceeds 20 KB')
    try:
        # SemDecide sends only text values, not arbitrary metadata/customer fields.
        matches, model, usage, latency = filter_records(provider, records, criterion, 'text')
        if len(matches) != len(records):
            raise ValueError('Missing answers')
        output = []
        for record, probability in matches:
            if isinstance(probability, bool) or not isinstance(probability, (int, float)) or not math.isfinite(probability) or not 0 <= probability <= 1:
                raise ValueError('Invalid probability')
            route = 'match' if probability >= threshold + margin else 'no_match' if probability <= threshold - margin else 'review'
            output.append({'id': record['id'], 'route': route, 'probability': probability})
        return {'records': output, 'model': model, 'usage': usage.as_dict(), 'latency_ms': latency, 'advisory_only': True}
    except Exception:
        # An entire failed batch is retained; no row silently disappears.
        return {'records': [{'id': i, 'route': 'provider_error', 'probability': None} for i in ids], 'advisory_only': True}


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    from reflex_guard.providers.typesafe import TypeSafeProvider
    parser = argparse.ArgumentParser(description='Live SemDecide batch; sends only text fields to TypeSafe.')
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--criterion', required=True)
    parser.add_argument('--data-class', choices=['public', 'synthetic', 'sanitized'], required=True)
    parser.add_argument('--live', action='store_true', help='Explicitly enable API calls; for offline use integrations.demo')
    args = parser.parse_args()
    if not args.live:
        parser.error('Add --live to send text to TypeSafe, or run python -m integrations.demo offline')
    with args.input.open('rb') as stream:
        raw = stream.read(30001)
    if len(raw) > 30000:
        parser.error('Input file exceeds 30 KB')
    rows = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    result = screen(rows, TypeSafeProvider(timeout=12, retries=0), args.criterion)
    result['data_class'] = args.data_class
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'output': str(args.output), 'records': len(result['records'])}))
    raise SystemExit(4 if any(r['route'] == 'provider_error' for r in result['records']) else 0)
