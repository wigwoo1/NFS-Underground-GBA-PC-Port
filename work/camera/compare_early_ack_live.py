import json,statistics
from pathlib import Path
root=Path('G:/EXTRA DATA DRIVE/Desktop/Games/Codex/NFSUG-Native-PC-Port/work/camera')
candidate=json.loads((root/'prototype-runs/early-ack-order-clock-cleanup-20261010.json').read_text())
baseline=json.loads(Path('prepared_hud_live_audit.json').read_text())

def summarize(a):
    r=json.loads(Path(a['source']).read_text())
    requests=[s for s in r['world_preparation_stage_samples'] if not s['history_only']]
    metrics={'request_service_ms':[(s['completed_ns']-s['started_ns'])/1e6 for s in requests],
             'queue_ms':[s['queue_wait_ns']/1e6 for s in requests],
             'ack_wait_ms':[x['ack_wait_ns']/1e6 for s in requests for x in s['terminal'][-1]['sample_transfer_rows']],
             'sample_prepare_ms':[x['prepare_since_ack_ns']/1e6 for s in requests for x in s['terminal'][-1]['sample_transfer_rows']]}
    stats={}
    for key,values in metrics.items():
        assert values
        values.sort();stats[key]=dict(count=len(values),median=statistics.median(values),p95=values[int(.95*(len(values)-1))],maximum=max(values))
    rows=[x for s in requests for x in s['parent_sample_rows']]
    stats['early_ack_samples']=sum(x['ack_sent_ns']<=x['publication_begin_ns'] for x in rows)
    stats['late_ack_samples']=sum(x['published_ns']<=x['ack_sent_ns'] for x in rows)
    return dict(source=a['source'],cadence=a['coverage']['active_intervals'],metrics=stats)

out=dict(candidate=summarize(candidate),baseline=summarize(baseline),scope='One sequential candidate then baseline comparison. Request metrics cover retained completed requests including startup; not causal proof or full60 qualification.')
assert out['candidate']['metrics']['early_ack_samples']>0
assert out['baseline']['metrics']['early_ack_samples']==0
Path('early_ack_candidate_baseline_comparison.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
