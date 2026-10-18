import json
from pathlib import Path
p=Path('work/camera/prototype-runs');r=json.loads((p/'owned-native-1791421794907737800.json').read_text());d=json.loads((p/'selected-sky-pixels-1791421795202590900.json').read_text());rows=d['records'];assert rows and not any('error' in x for x in rows)
committed={x['display_index']:x for x in r['presentation_samples'] if x.get('interpolated') and x.get('hidden_window_presented')}
for x in rows:
 c=committed[x['display_index']]
 for k in ('epoch','source_older','refresh','alpha'):assert x[k]==c[k]
 assert x['thread']==c['consumer_thread'] and x['selected_epoch']==c['epoch']
points=[pt for x in rows for pt in x['sky_reference_points']];mismatch=[dict(display=x['display_index'],point=pt) for x in rows for pt in x['sky_reference_points'] if not pt['stage_matches']]
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-sky-stage-crop-reference-20261007');cp.mkdir(exist_ok=True)
result=dict(result='PASS_STAGE_REFERENCE' if not mismatch else 'STAGE_MISMATCH',images=len(rows),stage_points=len(points),stage_matching=sum(pt['stage_matches'] for pt in points),final_matching=sum(pt['matches'] for pt in points),first_mismatches=mismatch[:20],scope='Actual selected queued image sky stage before geometry/HUD, original source-index palette reference; image identities match committed ledger. Diagnostic slow readbacks invalidate cadence; final differences can include occlusion.')
(cp/'stage-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
for name in ('owned-native-1791421794907737800.json','selected-sky-pixels-1791421795202590900.json','pool-cleanup-1791421794851974300.json'):(cp/name).write_bytes((p/name).read_bytes())
for name in ('live_source_sky_stage_candidate.py','run_live_sky_stage_candidate.py','run_queued_sky_stage_candidate.py'):(cp/name).write_bytes((Path('work/camera')/name).read_bytes())

