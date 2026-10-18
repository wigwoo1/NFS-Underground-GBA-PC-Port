"""Replay retained real DXGI spans with explicit submitted-image ownership."""
import json,sys
from pathlib import Path
from owned_dxgi_linked_span_totals_candidate import DisplayProgressTotals
r=json.loads(Path(sys.argv[1]).read_text());spans=r['dxgi_display_progress']['excess_refresh_spans'];counts=dict(valid=0,cross_generation=0,unmapped=0)
for row in spans:
 t=DisplayProgressTotals();key=tuple(row['key'])
 for endpoint,count,qpc in [('older_native_sample','older_present_count','start_qpc'),('newer_native_sample','newer_present_count','end_qpc')]:
  owner=row[endpoint];n=row[count]
  # Reconstruct retained native count ownership, not a new live observation.
  if owner is not None:t.submissions[n]=dict(owner)
  stats=[0,0,n+100,n,100 if endpoint.startswith('older') else 100+row['refresh_advance'],0,row[qpc],0,row['qpc_frequency']]
  t.observe(key,stats,dict(epoch=key[0],generation=key[1],display_index=99999))
 owners=[row['older_native_sample'],row['newer_native_sample']]
 valid=all(o is not None and (o['epoch'],o['generation'])==key for o in owners)
 assert len(t.spans)==int(valid)
 if valid:
  assert t.spans[0]['image_advance']==row['image_advance'] and t.spans[0]['refresh_advance']==row['refresh_advance'];counts['valid']+=1
 elif any(o is None for o in owners):counts['unmapped']+=1
 else:counts['cross_generation']+=1
# An unlinked report is explicitly excluded, not interpreted as smooth motion.
t=DisplayProgressTotals();t.observe((1,1),[0,0,100,1,2,0,10,0,100],dict(epoch=1,generation=1,display_index=0));assert t.unmapped_reports==1 and t.previous is None
out=dict(result='PASS_REPORTED_IMAGE_GENERATION_GUARD',retained_spans=len(spans),**counts,scope='Retained span replay; excludes mixed-generation/unknown image owners. Does not rebuild whole-run counters or certify scanout.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
