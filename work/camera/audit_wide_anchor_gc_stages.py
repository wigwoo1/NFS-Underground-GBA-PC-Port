import json,statistics
from pathlib import Path
p=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010');profile=json.loads((p/'wide-firstsample-profile30-audit.json').read_text());r=json.loads(Path(profile['raw']).read_text());rows=[]
def overlap(a,b,events):
 spans=sorted((max(a,x['start_ns']),min(b,x['end_ns'])) for x in events if max(a,x['start_ns'])<min(b,x['end_ns']));merged=[]
 for lo,hi in spans:
  if merged and lo<=merged[-1][1]:merged[-1]=(merged[-1][0],max(hi,merged[-1][1]))
  else:merged.append((lo,hi))
 return sum(hi-lo for lo,hi in merged)/1e6
for j in r['world_preparation_stage_samples']:
 t=j['terminal'][5]
 if not t['fine_trace'] or not t['sample_transfer_rows']:continue
 a=t['constructed_ns'];b=t['sample_transfer_rows'][0]['ready_ns'];events=t['child_gc_trace']['rows'];assert t['child_gc_trace']['dropped']==0
 sample=next(x for x in t['sample_timings'] if a<=x['started_ns']<=b<=x['completed_ns']);stages=[]
 for stage in sample['source_sample_stages']:
  start=stage['started_ns'];end=min(b,stage['completed_ns'])
  if end<start:continue
  assert stage['wall_ns']==stage['completed_ns']-start
  parts=[]
  for x in stage.get('anchor_stages',[]):
   assert start<=x['started_ns']<=x['completed_ns']<=stage['completed_ns']
   parts.append(dict(name=x['name'],wall_ms=x['wall_ns']/1e6,cycles=x['thread_cycles'],gc_ms=overlap(x['started_ns'],min(b,x['completed_ns']),events)))
  stages.append(dict(name=stage['name'],first_ready_clipped_wall_ms=(end-start)/1e6,cycles=stage['thread_cycles'],gc_ms=overlap(start,end,events),anchor_parts=parts))
 rows.append(dict(older=j['older'],newer=j['newer'],first_ready_ms=(b-a)/1e6,stages=stages))
assert len(rows)==207
worst=max(rows,key=lambda x:x['first_ready_ms']);ledger=r['live_observation_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0
joined=[dict(index=x['display_index'],gap_ms=x['interval_ns']/1e6) for x in ledger['records'] if x['transaction']['commit'][2:4]==[worst['older'],worst['newer']]]
assert joined
anchors=[s for x in rows for s in x['stages'] if s['name']=='model_anchors'];out=dict(result='PASS_WIDE_FIRST_READY_ANCHOR_GC_NESTING',jobs=len(rows),worst=worst,native_gap_joins=joined,anchor_median_ms=statistics.median(x['first_ready_clipped_wall_ms'] for x in anchors),rows=rows,scope='Exact first-ready clipping and unioned nested GC intersections over207finejobs; cycles on publication may includeack afterready, no exclusiveCPU attribution. Complete native longledger joins worst sourcepair. No performance change/60 qualification.')
(p/'wide-anchor-gc-stage-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
