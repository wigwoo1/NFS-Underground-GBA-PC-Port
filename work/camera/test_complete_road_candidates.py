import json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
from owned_motion_pairs import records
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());checks=[];matched=0
for f in r['wall_diagnostic_frames']:
 c=ClosedGraph.decode(Path(f['graph']).read_bytes());candidates=road_candidates(c,ClosedSceneMemory(c,rom));rows=[]
 for row in records(Path(f['regenerated']).read_bytes())['records']:
  if row['kind']!=1:continue
  choices=[x for x in candidates if x.descriptor_bytes==bytes(row['blocks'][9]) and x.vertices==bytes(row['blocks'][0])]
  assert len(choices)==1,(c.refresh,len(choices));x=choices[0];assert x.offsets==bytes(row['blocks'][1]);assert x.animation==bytes(row['blocks'][10][:8])
  if x.face is not None:assert x.face==bytes(row['blocks'][2])
  if x.texture is not None:assert bytes(row['blocks'][7])==x.texture
  assert struct.unpack_from('<HH',row['blocks'][3],36)==(struct.unpack_from('<H',x.material,26)[0],struct.unpack_from('<H',x.material,10)[0])
  matched+=1;rows.append(dict(descriptor=x.descriptor,secondary=x.secondary,missing=x.missing))
 checks.append(dict(refresh=c.refresh,candidates=len(candidates),complete=sum(not x.missing for x in candidates),captured=rows,missing_candidates=[dict(descriptor=x.descriptor,secondary=x.secondary,missing=x.missing) for x in candidates if x.missing]))
out=dict(result='PASS_COMPLETE_ROAD_CANDIDATE_OWNERSHIP',captured_records_matched=matched,checks=checks,scope='Raw road candidates independent of invocation visibility; reports incomplete assets explicitly, not GPU ready')
Path('work/camera/complete-road-candidate-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],matched);print([(x['refresh'],x['candidates'],x['complete']) for x in checks])
