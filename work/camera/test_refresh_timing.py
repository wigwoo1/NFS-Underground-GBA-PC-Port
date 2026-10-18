from pathlib import Path
import os,subprocess,csv,json,statistics,sys
p=Path('work/camera').resolve();duration=int(sys.argv[1]) if len(sys.argv)>1 else 15
env=dict(os.environ,NF_LIVE_HUD='1',NF_REFRESH_TRACE=str(p/'refresh-timing.csv'))
subprocess.check_call([sys.executable,str(p/'test_live_layer_sync.py'),str(duration),'--window-buffer'],env=env,stdout=subprocess.DEVNULL)
base=json.loads((p/'live-layer-sync-tests.json').read_text());rows=[{k:int(v) for k,v in r.items()} for r in csv.DictReader(open(p/'refresh-timing.csv'))]
assert len(rows)==base['refreshes'] and len(rows)>0
for i,r in enumerate(rows):
 assert r['index']==i and r['after']==r['before']+1 and r['end_ns']>=r['start_ns']
 assert r['keys']==(1|(32 if 180<=i<500 else 16 if 500<=i<720 else 0))
 assert r['scenes_after']>=r['scenes_before']
 if i:assert r['before']==rows[i-1]['after'] and r['epoch']==rows[i-1]['epoch'] and r['start_ns']>=rows[i-1]['end_ns']
def stats(rs):
 values=sorted((r['end_ns']-r['start_ns'])/1e6 for r in rs)
 return dict(count=len(values),median=statistics.median(values),p95=values[int(.95*len(values))],maximum=max(values),over_16_667ms=sum(v>1000/60 for v in values)) if values else dict(count=0)
published=[r for r in rows if r['scenes_after']>r['scenes_before']];other=[r for r in rows if r['scenes_after']==r['scenes_before']]
peak=sorted(rows,key=lambda r:r['end_ns']-r['start_ns'],reverse=True)[:8]
report=dict(result='PASS',duration_seconds=duration,exact_refresh_count=len(rows),every_refresh_once=True,refresh_and_input_continuity=True,all_refresh_ms=stats(rows),scene_publication_refresh_ms=stats(published),other_refresh_ms=stats(other),simulation_only_refresh_ms=stats([r for r in rows if not r['present']]),top_refreshes=[dict(index=r['index'],refresh=r['after'],duration_ms=(r['end_ns']-r['start_ns'])/1e6,present=r['present'],batch=r['batch'],published=r['scenes_after']-r['scenes_before']) for r in peak],live_test=base,scope='Every original refresh timed including simulation-only polls; identical final RAM vs original bridge; diagnostic timing with trace overhead, not actual scanout or smooth60fps proof')
(p/'refresh-timing-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='live_test'},indent=2))
