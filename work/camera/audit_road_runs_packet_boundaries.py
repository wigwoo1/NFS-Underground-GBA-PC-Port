import json,statistics
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/road-single-join-20261010')
output=[]
for label in ('baseline','candidate','reversecandidate','reversebaseline'):
 r=json.loads((cp/(label+'-live30-raw.json')).read_text());rows=[]
 for x in r['presentation_samples']:
  p=(x.get('prepared') or {}).get('bundle_transfer_profile')
  if not p:continue
  a,b,c,d=[p[k] for k in ('caller_begin_ns','native_begin_ns','native_end_ns','caller_end_ns')];assert a<=b<=c<=d and p['native_cycles']>=0
  stages=(x.get('prepared') or {}).get('consumer_stages',[])
  rows.append(dict(caller_ms=(d-a)/1e6,native_ms=(c-b)/1e6,before_ms=(b-a)/1e6,after_ms=(d-c)/1e6,cycles=p['native_cycles'],pair=[x['source_older'],x['refresh']],index=x['display_index'],consumer_stages=stages))
 assert rows
 output.append(dict(label=label,count=len(rows),median={k:statistics.median(x[k] for x in rows) for k in ('caller_ms','native_ms','before_ms','after_ms','cycles')},maximum={k:max(x[k] for x in rows) for k in ('caller_ms','native_ms','before_ms','after_ms','cycles')},worst=sorted(rows,key=lambda x:x['caller_ms'],reverse=True)[:3]))
out=dict(result='PASS_RETAINED_RENDERER_PACKET_BOUNDARIES',runs=output,scope='Last retained presentation windows only, four actual fullscene live runs. Native copy excludes subsequent double-to-float conversion; timing includes scheduling, no exclusive CPU/GIL or whole-run claim.')
(cp/'renderer-packet-boundaries.json').write_text(json.dumps(out,indent=2))
for x in output:print(x['label'],x['count'],x['median'],x['maximum'])
