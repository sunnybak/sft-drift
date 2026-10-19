"""Summarize a completed bounded corpus invocation; never dispatch generation.

Pass the wall-clock timing JSON recorded by the launcher explicitly. All paths are
local, and run IDs must identify existing ethical_stance_sft corpus runs.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sqlite3
import statistics


def summarize(root: Path, wall_seconds: float) -> dict:
    with sqlite3.connect(f'file:{root / "requests.sqlite"}?mode=ro', uri=True) as db:
        slots = db.execute('SELECT slot,result FROM requests').fetchall()
        pending = sum(value is None for _, value in slots)
        integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
    records = [json.loads(value) for _, value in slots if value is not None]
    fresh = [r for r in records if not r.get('cached')]
    documents = [json.loads(line) for path in (root/'shards').glob('*/documents.jsonl')
                 for line in path.read_text().splitlines()]
    usage = [r['response']['usage'] for r in fresh if r.get('response', {}).get('usage')]
    total_input = sum(u['input_tokens'] for u in usage)
    total_output = sum(u['output_tokens'] for u in usage)
    provider_counts = [r for r in fresh if r.get('token_count_preflight', {}).get('mode') == 'provider']
    deltas = [r['response']['usage']['input_tokens'] - r['token_count_preflight']['response']['input_tokens']
              for r in provider_counts if r.get('response', {}).get('usage')]
    count_attempts = sum(r.get('token_count_preflight', {}).get('mode') == 'provider'
                         or 'error' in r.get('token_count_preflight', {}) for r in fresh)
    lengths = [d['tokens'] for d in documents]
    timings = [r['latency_seconds'] for r in fresh if 'latency_seconds' in r]
    requests = sorted((r['dispatch_unix_seconds'], r['rate_reserved_tokens']) for r in fresh
                      if 'dispatch_unix_seconds' in r)
    edges=sorted(edge for r in fresh if 'dispatch_unix_seconds' in r for edge in
                 [(r['dispatch_unix_seconds'],1),
                  (r['dispatch_unix_seconds']+r['latency_seconds'],-1)])
    active=peak_active=0
    for _,change in edges:
        active+=change
        peak_active=max(peak_active,active)
    left = reserved = peak_tokens = peak_requests = 0
    for right, (time, tokens) in enumerate(requests):
        reserved += tokens
        while requests[left][0] <= time-60:
            reserved -= requests[left][1]
            left += 1
        peak_tokens = max(peak_tokens, reserved)
        peak_requests = max(peak_requests, right-left+1)
    return {'run_id':root.name, 'integrity_check':integrity, 'pending':pending,
        'wall_seconds':wall_seconds, 'documents':len(documents), 'logical_generation_calls':len(records),
        'fresh_generation_calls':len(fresh), 'local_replays':len(records)-len(fresh),
        'count_endpoint_attempts':count_attempts, 'count_endpoint_successes':len(provider_counts),
        'count_deltas':{'min':min(deltas,default=0),'max':max(deltas,default=0)},
        'errors':[r['error'] for r in fresh if r.get('error')],
        'generation_cost_usd':sum(r.get('cost_usd') or 0 for r in fresh),
        'uncertain_cost_upper_bound':sum(r.get('uncertain_cost_upper_bound') or 0 for r in fresh),
        'provider_input_tokens':total_input,'provider_output_tokens':total_output,
        'generation_rpm_over_full_invocation':len(fresh)*60/wall_seconds,
        'http_rpm_over_full_invocation':(len(fresh)+count_attempts)*60/wall_seconds,
        'usage_tpm_over_full_invocation':(total_input+total_output)*60/wall_seconds,
        'peak_simultaneous_generation_calls':peak_active,
        'generation_peak_rolling_minute_calls':peak_requests,
        'generation_peak_rolling_minute_reserved_tokens':peak_tokens,
        'rate_reservation_tokens_total':sum(r.get('rate_reserved_tokens',0) for r in fresh),
        'mean_generation_latency_seconds':statistics.mean(timings) if timings else None,
        'lengths':{'min':min(lengths,default=0),'max':max(lengths,default=0),
                   'mean':statistics.mean(lengths) if lengths else None},
        'mechanical_flagged_documents':sum(bool(d['mechanical_flags']) for d in documents),
        'limits':'Short finite run includes startup, planning and drain; not steady-state saturation. '
                 'Generation latency excludes token-count preflight. Token counts are provider usage, '
                 'not final Qwen lengths. No full agent content review was performed for this throughput check.'}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--timings',type=Path,required=True)
    args=parser.parse_args()
    if Path(args.run_id).name != args.run_id or not args.run_id.startswith('ethics_sft_'):
        parser.error('Expected an ethics_sft_ run ID')
    base=Path(__file__).resolve().parents[1]
    root=base/'data/generated/ethical_stance_sft'/args.run_id
    timing=json.loads(args.timings.read_text())[args.run_id+'_generate']
    if timing['returncode']:
        parser.error('Expected a completed successful invocation')
    result=summarize(root,timing['elapsed_seconds'])
    output=base/'data/results/ethical_stance_sft'/args.run_id
    (output/'throughput.json').write_text(json.dumps(result,indent=2)+'\n')
    (output/'throughput.md').write_text('# Bounded throughput check\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
