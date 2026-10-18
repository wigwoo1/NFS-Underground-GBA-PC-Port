from pathlib import Path
import ctypes as C,struct,json,time,hashlib
from owned_motion_pairs import records
from owned_source_native_depth_rectangle_candidate import OwnedProjectionTable,SourceFaceDeterminants
from owned_source_depth_rectangle_candidate import SourceFaceDeterminants as Reference
p=Path('work/camera');r=json.loads((p/'prototype-runs/owned-native-1791267744113946700.json').read_text());d=C.CDLL(str((p/'owned-sky-source-face-candidate.dll').resolve()));raw=(C.c_uint32*32768)(*struct.unpack('<32768I',(p/'road-correction-reciprocal.bin').read_bytes()[:131072]));owner=OwnedProjectionTable(raw);checks=0
for capture in r['wall_diagnostic_frames']:
 for row in records(Path(capture['regenerated']).read_bytes())['records']:
  if row['kind']!=3:continue
  ref=Reference(row,row,d,raw);obj=SourceFaceDeterminants(row,row,d,owner);assert obj.native_table is owner.native
  for alpha in (0,.125,.5,.75,1):
   m=obj.matrices[0];assert obj.combined_decisions(m,alpha,(0,0,240,160))==(ref.decisions(m,alpha),ref.rectangle_decisions(m,alpha,(0,0,240,160)));checks+=len(obj.faces)
original=owner.native[100];raw[100]^=0xffffffff;assert owner.native[100]==original;raw[100]=original
timings={}
for label,table in (('private_copy_each_constructor',raw),('shared_private_owner',owner)):
 started=time.perf_counter_ns()
 for _ in range(100):SourceFaceDeterminants(row,row,d,table)
 timings[label]=(time.perf_counter_ns()-started)/1e6
hashes=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-committed-sample-20261006/protected-hashes.json').read_text());assert all(hashlib.sha256(Path(k).read_bytes()).hexdigest().upper()==v for k,v in hashes.items())
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/shared-projection-table-20261007');cp.mkdir(exist_ok=True);result=dict(result='PASS_SHARED_PRIVATE_PROJECTION_TABLE',face_decision_checks=checks,caller_table_mutation_isolated=True,constructor_100_calls_ms=timings,protected_assets='PASS',scope='Captured same-pose fractional policy decision equivalence and private resource sharing; component benchmark, not live cadence proof.');(cp/'tests.json').write_text(json.dumps(result,indent=2))
for name in ('owned_source_native_depth_rectangle_candidate.py','owned_precomputed_source_samples_candidate.py','test_shared_projection_table.py'):(cp/name).write_bytes((p/name).read_bytes())
print(json.dumps(result,indent=2))
