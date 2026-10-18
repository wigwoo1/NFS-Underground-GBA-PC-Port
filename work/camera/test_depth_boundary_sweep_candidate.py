"""Sweep captured depth transition using actual complete-world matrices."""
import json,ctypes as C,struct
from pathlib import Path
import owned_source_presentation_batch_candidate as batch
from owned_source_depth_transition_candidate import SourceFaceDeterminants
from owned_precomputed_source_samples_candidate import projection_table_owner
from owned_motion_pairs import records
built={}
def build(a,b,d,table):
 c=SourceFaceDeterminants(a,b,d,table);built[a['key']]=c;return c
batch.SourceFaceDeterminants=build
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')","folder=Path('work/camera/prototype-runs/fullscene-failure-1791505088433840800')");ns={};checks=[]
try:
 exec(compile(source,'capture_setup','exec'),ns);gpu=C.CDLL(str(Path('work/camera/owned-sky-source-context-candidate.dll').resolve()));anchors,classifiers=batch.prepare_source_models(ns['prepared'],gpu,projection_table_owner());targets={k:c for k,c in built.items() if c.single_endpoint};assert len(targets)==1
 for n in range(101):
  a=n/100;frame,camera,models,bounds,detail=ns['prepared'].sample(a);rows=records(frame)['records']
  for k,c in targets.items():
   positions=[i for i,r in enumerate(rows) if r['key']==k]
   if not positions:checks.append(dict(alpha=a,present=False));continue
   assert len(positions)==1;i=positions[0];raw=struct.unpack('<12i',rows[i]['blocks'][2]);m=tuple(v/16384 if j<9 else float(v) for j,v in enumerate(raw)) if models is None else tuple(models[i*12:i*12+12]);depths=[m[11]+x*m[2]+y*m[5]+z*m[8] for x,y,z in c.vertices];b=(-32768,32768,-32768,32768) if bounds is None else bounds[i*4:i*4+4];faces,rect=c.combined_decisions(m,a,(b[0],b[2],b[1],b[3]));valid=c.depth_valid(m,a)
   if not valid:assert not any(faces) and all(x==4 for x in rect)
   checks.append(dict(alpha=a,present=True,minimum_depth=min(depths),maximum_depth=max(depths),depth_valid=valid,selected_faces=sum(v and r!=4 for v,r in zip(faces,rect))))
finally:
 for name in ('prepared','history'):
  if ns.get(name):ns[name].close()
out=dict(result='PASS_CAPTURED_DEPTH_BOUNDARY_SWEEP',samples=len(checks),present_samples=sum(x['present'] for x in checks),rejected_present_samples=sum(x['present'] and not x['depth_valid'] for x in checks),checks=checks,scope='101 complete-world poses and classifier decisions. Internal gate consistency, not independent visibility/pixel fidelity or continuous-time crossing proof.')
Path('work/camera/prototype-runs/native-depth-boundary-sweep-20261008.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='checks'})
