import json,sys
from pathlib import Path
raw=json.loads(Path(sys.argv[1]).read_text());trace=json.loads(Path(sys.argv[2]).read_text());rows=trace['rows'];assert rows and len(rows)<=180 and trace['capacity']==180
keys={tuple(r['identity']):r for r in rows};assert len(keys)==len(rows) and [r['identity'][2] for r in rows]==list(range(rows[0]['identity'][2],181))
for row in rows:
 t=row['caller_timing'];p=row['present_stages'];assert t['draw_begin_ns']<=t['draw_end_ns']<=p['begin']<=p['pumped']<=p['presented']<=p['queried']<=row['commit_ns']
 assert row['wait'][1]==row['deadline_ns'] and row['wait'][2]>=row['deadline_ns']
holds=[]
for span in raw['dxgi_display_progress']['excess_refresh_spans']:
 newer=span['newer_native_sample'];assert newer
 k=(newer['epoch'],newer['generation'],newer['display_index']);neighbors=[]
 for index in range(k[2]-3,k[2]+4):
  r=keys.get((k[0],k[1],index))
  if r is None:continue
  prior=keys.get((k[0],k[1],index-1));t=r['caller_timing'];p=r['present_stages']
  neighbors.append(dict(identity=r['identity'],source_pair=[r['source_older'],r['source_newer']],alpha=r['alpha'],commit_gap_ms=(r['commit_ns']-prior['commit_ns'])/1e6 if prior else None,deadline_step_ms=(r['deadline_ns']-prior['deadline_ns'])/1e6 if prior else None,draw_ms=(t['draw_end_ns']-t['draw_begin_ns'])/1e6,present_entry_after_deadline_ms=(p['begin']-r['deadline_ns'])/1e6,present_wait_ms=(p['presented']-p['pumped'])/1e6,commit_after_deadline_ms=(r['commit_ns']-r['deadline_ns'])/1e6,statistics=r['statistics']))
 holds.append(dict(reported_span=span,trace_has_newer_frame=k in keys,neighbors=neighbors))
out=dict(result='VERIFIED_EARLY_PRESENTATION_TIMING_TRACE',rows=len(rows),holds=holds,scope='Complete observed early callback identities through index180; initial callback start explicitly retained with validated timing order. Nearby reported hold association and deadline offsets; no exclusive GPU/compositor/CPU cause or physical scanout certification.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print('holds',len(holds));print(json.dumps(holds,indent=2))

