import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());assert r['gc_trace_dropped']==0
rows=[x for x in r['presentation_samples'] if x.get('native_result')==1 and x.get('prepared',{}).get('hud_lease_stages')]
assert rows
intervals={'snapshot':('snapshot_begin_ns','snapshot_end_ns'),'bind':('bind_begin_ns','callback_begin_ns'),'callback':('callback_begin_ns','callback_end_ns'),'release':('callback_end_ns','release_end_ns')}
def stats(v):
 return dict(count=len(v),median_ms=statistics.median(v)/1e6,max_ms=max(v)/1e6) if v else dict(count=0)
groups={}
for new in [False,True]:
 selected=[x for x in rows if x['prepared']['hud_lease_stages']['snapshot_new']==new]
 groups['new' if new else 'reused']={key:stats([x['prepared']['hud_lease_stages'][b]-x['prepared']['hud_lease_stages'][a] for x in selected]) for key,(a,b) in intervals.items()}
slow=[]
for x in sorted(rows,key=lambda x:x['prepared']['source_prepare_ns'],reverse=True)[:8]:
 p=x['prepared']['hud_lease_stages'];entry=dict(index=x['display_index'],snapshot_new=p['snapshot_new'],source_ms=x['prepared']['source_prepare_ns']/1e6,stages={})
 for key,(a,b) in intervals.items():
  overlaps=[dict(generation=g['generation'],overlap_ms=(min(p[b],g['end_ns'])-max(p[a],g['start_ns']))/1e6) for g in r['gc_collection_samples'] if min(p[b],g['end_ns'])>max(p[a],g['start_ns'])]
  entry['stages'][key]=dict(duration_ms=(p[b]-p[a])/1e6,gc_overlaps=overlaps)
 slow.append(entry)
out=dict(result='RETAINED_LIVE_HUD_STAGE_COST',groups=groups,slowest=slow,scope='Retained120successful rows; stage wall intervals include scheduling/GIL waits. GC overlap correlation is not exclusive causal attribution. No fullscene60fps proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(groups,indent=2));print('slowest',json.dumps(slow[0]))
