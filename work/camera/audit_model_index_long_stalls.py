import json,re
from pathlib import Path
root=Path('G:/EXTRA DATA DRIVE/Desktop/Games/Codex/NFSUG-Native-PC-Port/work/camera')
results={}
for mode in ('base','candidate'):
    a=json.loads((root/f'prototype-runs/model-index-{mode}60-clock-cleanup-20261010.json').read_text())
    r=json.loads(Path(a['source']).read_text())
    raw=Path(a['log']).read_bytes();log=raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig')
    gc=json.loads(Path(re.search(r'PARENT_GC_TRACE (.+)',log).group(1).strip()).read_text());assert gc['dropped']==0
    w=r['live_observation_stats']['whole_run_api_intervals'];ledger=w['native_commit_long_intervals']
    assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])==a['coverage']['active_intervals']['over25']
    rows=[]
    for sample in ledger['records']:
        c=sample['caller_timing'];s=sample['caller_stages'];p=sample['prepared'];d=p['renderer_dispatch']
        spans={'take':(s['preparation_take_begin_ns'],s['preparation_take_end_ns']),
               'hud_wait':(s['hud_prefetch_wait_begin_ns'],s['hud_prefetch_wait_end_ns']),
               'draw':(c['draw_begin_ns'],c['draw_end_ns']),
               'job':(d['started_ns'],d['completed_ns']),
               'present':(c['present_begin_ns'],c['present_end_ns'])}
        parts={}
        for name,(start,end) in spans.items():
            assert start<=end
            parts[name]=dict(ms=(end-start)/1e6,gc=[dict(generation=e['generation'],ms=(e['end_ns']-e['start_ns'])/1e6) for e in gc['events'] if max(start,e['start_ns'])<min(end,e['end_ns'])])
        pair=sample['transaction']['commit'][2:4]
        requests=[x for x in r['world_preparation_stage_samples'] if [x['older'],x['newer']]==pair]
        rows.append(dict(index=sample['display_index'],gap_ms=sample['interval_ns']/1e6,pair=pair,parts=parts,
                         request_matches=len(requests),consumer_stages=[dict(stage=x['stage'],ms=x['elapsed_ns']/1e6) for x in p['consumer_stages']]))
    results[mode]=rows
out=dict(results=results,scope='Complete live over25ms retained population for each run, no dropped records. Nested spans not additive; GC overlap association. No scanout or full60 claim.')
Path('model_index_long_stalls.json').write_text(json.dumps(out,indent=2))
for mode,rows in results.items():
    for row in rows:print(json.dumps(dict(mode=mode,**row)))
