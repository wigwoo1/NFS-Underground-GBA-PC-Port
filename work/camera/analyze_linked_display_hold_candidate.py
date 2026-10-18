"""Join reported display holds to complete long API intervals by identity/time."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());d=r['dxgi_display_progress'];a=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']
assert d['excess_refresh_spans_dropped']==0 and a['dropped']==0
rows=[]
for span in d['excess_refresh_spans']:
 key=tuple(span['key']);old=span['older_native_sample'];new=span['newer_native_sample']
 assert old is not None and new is not None
 assert (old['epoch'],old['generation'])==(new['epoch'],new['generation'])==key
 assert new['display_index']>old['display_index'] and span['refresh_advance']>span['image_advance']>0
 start=span['start_qpc']*1000000000//span['qpc_frequency'];end=span['end_qpc']*1000000000//span['qpc_frequency'];matches=[]
 for gap in a['records']:
  if (gap['epoch'],gap['generation'])!=key:continue
  overlap=max(0,min(end,gap['end_ns'])-max(start,gap['begin_ns']))
  # Clock overlap and ordinal adjacency are separate associations.
  nearby=old['display_index']<=gap['display_index']<=new['display_index']
  if overlap or nearby:
   lease=gap['hud_lease_stages'];profile=lease.get('native_callback_profile',{})
   matches.append(dict(index=gap['display_index'],clock_overlap_ms=overlap/1e6,ordinal_nearby=nearby,api_gap_ms=gap['interval_ns']/1e6,present_ms=(gap['present_end_ns']-gap['present_begin_ns'])/1e6,consumer_stages=gap['consumer_stages']))
 rows.append(dict(key=list(key),older_index=old['display_index'],newer_index=new['display_index'],images=span['image_advance'],refreshes=span['refresh_advance'],reported_span_ms=(end-start)/1e6,matches=matches))
out=dict(result='PASS_LINKED_DISPLAY_HOLD_JOIN',reported_hold_spans=len(rows),single_image_holds=sum(x['images']==1 for x in rows),spans_with_long_interval_association=sum(bool(x['matches']) for x in rows),rows=rows,scope='Correct-generation reported-image ownership, QPC clock overlap and ordinal adjacency separately marked. DXGI query gaps may omit reports; only >33.333ms API gaps retained. Association is not causal proof or exact physical pixel scanout.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))
