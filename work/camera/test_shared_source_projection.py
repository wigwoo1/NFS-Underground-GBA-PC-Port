import ctypes as C,json,struct,hashlib
from pathlib import Path
from owned_motion_pairs import records
from owned_source_native_depth_rectangle_candidate import SourceFaceDeterminants
p=Path('work/camera');r=json.loads((p/'prototype-runs/owned-native-1791267744113946700.json').read_text());d=C.CDLL(str((p/'owned-sky-source-face-candidate.dll').resolve()));table=(C.c_uint32*32768)(*struct.unpack('<32768I',(p/'road-correction-reciprocal.bin').read_bytes()[:131072]));checks=0;calls=0
for capture in r['wall_diagnostic_frames']:
 for row in records(Path(capture['regenerated']).read_bytes())['records']:
  if row['kind']!=3:continue
  obj=SourceFaceDeterminants(row,row,d,table)
  for alpha in (0,.125,.25,.5,.75,.999999,1):
   m=list(obj.matrices[0]);m[9]+=alpha;m[10]-=alpha;m[11]+=alpha
   for rect in ((0,0,240,160),(117,0,125,160),(4,4,6,6),(0,0,0,0)):
    expected=(obj.decisions(m,alpha),obj.rectangle_decisions(m,alpha,rect));original=obj.projected;counter=[0]
    def counted(*args):
     counter[0]+=1;return original(*args)
    obj.projected=counted
    try:actual=obj.combined_decisions(m,alpha,rect)
    finally:obj.projected=original
    assert actual==expected and counter[0]==1
    checks+=len(actual[0]);calls+=1
hp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-committed-sample-20261006/protected-hashes.json');hashes=json.loads(hp.read_text());assert all(hashlib.sha256(Path(k).read_bytes()).hexdigest().upper()==v for k,v in hashes.items())
root=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/shared-source-projection-20261007');root.mkdir(exist_ok=True)
result=dict(result='PASS',face_rectangle_checks=checks,combined_calls=calls,native_projections_per_combined_call=1,previous_projections_per_call=2,protected_assets='PASS',scope='Captured model poses with fractional translation and four rectangle domains; exact equivalence to separate decisions, not live cadence proof.')
(root/'tests.json').write_text(json.dumps(result,indent=2))
for name in ('owned_source_native_depth_rectangle_candidate.py','owned_source_face_mask_candidate.py','test_shared_source_projection.py'):(root/name).write_bytes((p/name).read_bytes())
with Path('outputs/nfsug-native-renderer/camera-research/STATUS.md').open('ab') as f:f.write(('\n\n## 2026-10-07 - shared source classification projection\nSeparate native source candidate now shares one native vertex projection between face determinants and rectangle membership, reducing two identical projection calls to one per model/sample. Exact equivalence verified for '+str(checks)+' face/rectangle comparisons across '+str(calls)+' combined calls, seven fractions and four rectangle domains in captured models. Counted calls confirm one projection each. Protected ROM/save/stable fallback hashes PASS; default unchanged. Checkpoint shared-source-projection-20261007 retains test/source/results. This component reduction does not establish live cadence; prior candidate still has long presentation gaps. Next dependency retain source metadata and prepare masks off GPU thread, resolve unpaired model deactivation at 9111..9115, then visible pause/steering/original timing/cadence verification. Full scene fidelity, physical 4K and Xbox remain unverified; entire project approximately 65%, high uncertainty; goal active.\n').encode())
print(json.dumps(result,indent=2))
