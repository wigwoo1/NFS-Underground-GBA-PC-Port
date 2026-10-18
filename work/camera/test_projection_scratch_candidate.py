import ctypes as C,json,struct,concurrent.futures
from pathlib import Path
import owned_source_projection_scratch_candidate as candidate
from owned_source_native_depth_rectangle_candidate import SourceFaceDeterminants,OwnedProjectionTable
from owned_motion_pairs import records
root=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-source-context-20261007/failure-snapshot');ends=[{x['key']:x for x in records((root/(n+'.frame.bin')).read_bytes())['records'] if x['kind']==3} for n in ('older','newer')];gpu=C.CDLL(str(Path('work/camera/owned-sky-source-context-candidate.dll').resolve()));table=OwnedProjectionTable(struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]));checks=[]
for key in ends[0].keys()&ends[1].keys():
 a=SourceFaceDeterminants(ends[0][key],ends[1][key],gpu,table);b=candidate.SourceFaceDeterminants(ends[0][key],ends[1][key],gpu,table);ids=tuple(C.addressof(v) for v in (b._matrix_buffer,b._center_buffer,b._projection_buffer));jobs=[]
 for i in range(41):
  alpha=i/40;m=tuple((1-alpha)*x+alpha*y for x,y in zip(*a.matrices));expected=a.projected(m,a.scales[0],a.centers[0]);assert expected==b.projected(m,b.scales[0],b.centers[0]);assert a.decisions(m,alpha)==b.decisions(m,alpha);assert a.combined_decisions(m,alpha,(0,0,240,160))==b.combined_decisions(m,alpha,(0,0,240,160));jobs.append((m,expected))
 def run(job):
  m,expected=job;assert b.projected(m,b.scales[0],b.centers[0])==expected
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(run,jobs*3))
 assert ids==tuple(C.addressof(v) for v in (b._matrix_buffer,b._center_buffer,b._projection_buffer))
 snapshot=b.projected(jobs[0][0],b.scales[0],b.centers[0]);b.projected(jobs[-1][0],b.scales[0],b.centers[0]);assert snapshot==jobs[0][1]
 saved=candidate._project;candidate._project=lambda *args:1
 try:
  try:b.projected(jobs[0][0],b.scales[0],b.centers[0])
  except ValueError:pass
  else:raise AssertionError('Native failure accepted')
 finally:candidate._project=saved
 run(jobs[0]);checks.append(dict(key=key,vertices=len(b.vertices),calls=164,buffer_addresses_stable=True,snapshot_immutable=True,failure_lock_released=True))
assert checks
out=dict(result='PASS',checks=checks,scope='Actual source projection/face/rectangle exact parity and concurrent buffer serialization; no live performance claim');Path('work/camera/projection-scratch-tests.json').write_text(json.dumps(out,indent=2));print(out)
