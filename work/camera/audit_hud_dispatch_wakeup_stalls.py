import json
from pathlib import Path
root=Path(r'G:\EXTRA DATA DRIVE\Desktop\Games\Codex\NFSUG-Native-PC-Port\work\camera\prototype-runs')
out={}
for label in ('base','candidate'):
    manifest=json.loads((root/f'model-index-{label}60-clock-cleanup-20261010.json').read_text())
    raw=json.loads(Path(manifest['source']).read_text())
    ledger=raw['live_observation_stats']['whole_run_api_intervals']['native_commit_long_intervals']
    assert ledger['dropped']==0 and len(ledger['records'])==manifest['coverage']['active_intervals']['over25']==3
    rows=[]
    for x in ledger['records']:
        s=x['caller_stages']; d=s['hud_prefetch_dispatch']; prep=x['prepared']['renderer_dispatch']
        b,e=s['hud_prefetch_wait_begin_ns'],s['hud_prefetch_wait_end_ns']
        q,t,c=d['submitted_ns'],d['started_ns'],d['completed_ns']
        assert q<=b<=t<=c<=e, (label,x['display_index'],q,b,t,c,e)
        rows.append(dict(index=x['display_index'],gap_ms=x['interval_ns']/1e6,hud_wait_ms=(e-b)/1e6,queue_delay_ms=(t-q)/1e6,worker_task_ms=(c-t)/1e6,waiter_resume_after_completion_ms=(e-c)/1e6,submission_to_wait_begin_ms=(b-q)/1e6,prepare_submit_after_wait_ms=(prep['submitted_ns']-e)/1e6,prepare_queue_ms=(prep['started_ns']-prep['submitted_ns'])/1e6,prepare_job_ms=(prep['completed_ns']-prep['started_ns'])/1e6))
    out[label]=rows
payload=dict(results=out,scope='All retained >25ms native intervals in matched 60s runs; exact HUD wait and worker dispatch nesting. This partitions elapsed timestamps, not CPU causality or hardware scanout.')
path=root/'model-index-hud-wakeup-decomposition-20261010.json';path.write_text(json.dumps(payload,indent=2))
for label,rows in out.items():
    for row in rows: print(label,json.dumps(row,separators=(',',':')))
print('saved',path)
