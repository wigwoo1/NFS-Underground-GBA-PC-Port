import json
from pathlib import Path
p=Path('work/camera/prototype-runs');r=json.loads((p/'owned-native-1791421226810798200.json').read_text());d=json.loads((p/'selected-sky-pixels-1791421226982063100.json').read_text());rows=d['records'];assert len(rows)==60 and not any('error' in x for x in rows)
committed={x['display_index']:x for x in r['presentation_samples'] if x.get('hidden_window_presented') and x.get('interpolated')};checks=[]
for x in rows:
 c=committed[x['display_index']]
 for key in ('epoch','source_older','refresh','alpha'):assert x[key]==c[key]
 assert x['selected_epoch']==c['epoch'] and x['thread']==c['consumer_thread']
for a,b in zip(rows,rows[1:]):
 if (a['source_older'],a['refresh'])==(b['source_older'],b['refresh']) and a['alpha']!=b['alpha']:
  checks.append(dict(previous=a['display_index'],current=b['display_index'],changed=a['sha256']!=b['sha256'],fractions=[a['fraction'],b['fraction']]))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-selected-sky-pixels-20261007');cp.mkdir(exist_ok=True)
result=dict(result='PASS_ATTRIBUTION',selected_images=len(rows),same_pair_transitions=len(checks),changed_crops=sum(x['changed'] for x in checks),checks=checks,scope='Exact committed identity/owner-thread attribution for selected 4K queue target readback; crop includes possible foreground and changes alone do not certify sky-only motion. Readback timing not valid gameplay cadence proof.')
(cp/'attribution.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
for name in ('owned-native-1791421226810798200.json','selected-sky-pixels-1791421226982063100.json','pool-cleanup-1791421226779214800.json'):(cp/name).write_bytes((p/name).read_bytes())
for name in ('run_source_sky_pixels_candidate.py','live_source_sky_pixels_candidate.py'):(cp/name).write_bytes((Path('work/camera')/name).read_bytes())

