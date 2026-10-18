import json
from pathlib import Path
p=Path('work/camera/prototype-runs');r=json.loads((p/'owned-native-1791421310200086600.json').read_text());d=json.loads((p/'selected-sky-pixels-1791421310346950100.json').read_text());rows=d['records'];assert len(rows)==60 and not any('error' in x for x in rows)
committed={x['display_index']:x for x in r['presentation_samples'] if x.get('hidden_window_presented') and x.get('interpolated')}
for x in rows:
 c=committed[x['display_index']]
 for k in ('epoch','source_older','refresh','alpha'):assert x[k]==c[k]
 assert x['thread']==c['consumer_thread'] and x['selected_epoch']==c['epoch']
matched=sum(pt['matches'] for x in rows for pt in x['sky_reference_points']);total=sum(len(x['sky_reference_points']) for x in rows);changes=[]
for a,b in zip(rows,rows[1:]):
 if (a['source_older'],a['refresh'])!=(b['source_older'],b['refresh']):continue
 count=0
 for pa,pb in zip(a['sky_reference_points'],b['sky_reference_points']):
  assert (pa['x'],pa['y'])==(pb['x'],pb['y'])
  if pa['matches'] and pb['matches'] and pa['expected']!=pb['expected'] and pa['actual']!=pb['actual']:count+=1
 changes.append(dict(previous=a['display_index'],current=b['display_index'],reference_matching_changed_points=count))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-sky-color-reference-20261007');cp.mkdir(exist_ok=True)
result=dict(result='AUDITED',images=len(rows),matched_points=matched,total_points=total,matching_changed_transitions=sum(x['reference_matching_changed_points']>0 for x in changes),same_pair_transitions=len(changes),changes=changes,scope='Selected committed image source-index/per-scanline-palette color comparison within1channel unit. Matching colors support sky correspondence but are not an independent occlusion mask; readback/reference work affects cadence.')
(cp/'reference-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='changes'}))
for name in ('owned-native-1791421310200086600.json','selected-sky-pixels-1791421310346950100.json','pool-cleanup-1791421310173524800.json'):(cp/name).write_bytes((p/name).read_bytes())
for name in ('run_source_sky_pixels_candidate.py','live_source_sky_pixels_candidate.py'):(cp/name).write_bytes((Path('work/camera')/name).read_bytes())
