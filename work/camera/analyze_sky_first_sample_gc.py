"""Bounded first-sample stage/GC overlap audit; no cadence qualification."""
import json,sys
from pathlib import Path
d=json.loads(Path(sys.argv[1]).read_text())
jobs=[]
for s in d['world_preparation_stage_samples']:
 if (s['older'],s['newer'])!=(10902,10907):continue
 b=s['terminal'][5]
 assert s['terminal'][2]=='complete'
 a=next(x for x in b['sample_timings'][0]['source_sample_stages'] if x['name']=='model_anchors')
 m=next(x for x in a['anchor_stages'] if x['name']=='record_metadata')
 u=next(x for x in m['metadata_stages'] if x['name']=='uncached_decode')
 assert b['child_gc_trace']['dropped']==0
 overlaps=[]
 for g in b['child_gc_trace']['rows']:
  assert g['end_ns']>=g['start_ns']
  overlap=max(0,min(u['completed_ns'],g['end_ns'])-max(u['started_ns'],g['start_ns']))
  if overlap:overlaps.append(dict(generation=g['generation'],duration_ms=(g['end_ns']-g['start_ns'])/1e6,overlap_ms=overlap/1e6,collected=g['collected']))
 jobs.append(dict(older=s['older'],newer=s['newer'],anchor_ms=a['wall_ns']/1e6,decode_ms=u['wall_ns']/1e6,gc_overlaps=overlaps))
assert len(jobs)==1 and any(x['generation']==2 and x['overlap_ms']>25 for x in jobs[0]['gc_overlaps'])
out=dict(result='PASS_BOUNDED_STAGE_GC_OVERLAP',jobs=jobs,cadence_qualified=False,scope='One retained source pair; temporal overlap does not establish exclusive cause or a collection-policy fix.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2))
print(json.dumps(out))
