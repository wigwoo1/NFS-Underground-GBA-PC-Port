import ctypes as C,json,struct,math
from pathlib import Path
from owned_motion_pairs import records
from owned_source_rectangle_candidate import SourceFaceDeterminants
p=Path('work/camera');report=json.loads((p/'prototype-runs/owned-native-1791267744113946700.json').read_text());frames=report['wall_diagnostic_frames'];d=C.CDLL(str((p/'owned-sky-camera-anchor-candidate.dll').resolve()));table=(C.c_uint32*32768)(*struct.unpack('<32768I',(p/'road-correction-reciprocal.bin').read_bytes()[:131072]));checks=0;maximum=0;zero_faces=0;near_disagreements=0;models=0;rectangle_checks=0
for fa,fb in zip(frames,frames[1:]):
 a={r['key']:r for r in records(Path(fa['regenerated']).read_bytes())['records'] if r['kind']==3};b={r['key']:r for r in records(Path(fb['regenerated']).read_bytes())['records'] if r['kind']==3}
 for key in a.keys()&b.keys():
  candidate=SourceFaceDeterminants(a[key],b[key],d,table);models+=1
  for endpoint in (0,1):
   actual=candidate.sample(candidate.matrices[endpoint],endpoint)
   row=a[key] if endpoint==0 else b[key];rect=struct.unpack('<4i',row['blocks'][9]);rect_c=(C.c_int32*4)(*rect);points=candidate.endpoint_points[endpoint];raw=struct.pack('<'+'h'*len(points)*2,*(v for pair in points for v in pair));classifications=candidate.rectangle_decisions(candidate.matrices[endpoint],endpoint,rect)
   d.nfs_model_polygon_classify.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
   for ids,cl in zip(candidate.faces,classifications):
    indices=(C.c_uint16*len(ids))(*ids);out=C.c_int();assert d.nfs_model_polygon_classify(raw,len(points),indices,len(ids),rect_c,C.byref(out))==1;assert cl==out.value;rectangle_checks+=1
   for x,y in zip(actual,candidate.exact[endpoint]):
    maximum=max(maximum,abs(x-y));assert abs(x-y)<1e-9;checks+=1;zero_faces+=y==0
   alpha=1e-9 if endpoint==0 else 1-1e-9;m=tuple((1-alpha)*x+alpha*y for x,y in zip(*candidate.matrices));near=candidate.sample(m,alpha)
   near_disagreements+=sum((x>=0)!=(y>=0) for x,y in zip(near,candidate.exact[endpoint]))
  for alpha in (.25,.5,.75):
   m=tuple((1-alpha)*x+alpha*y for x,y in zip(*candidate.matrices));assert all(math.isfinite(x) for x in candidate.sample(m,alpha))
  for invalid in (-.1,1.1,float('nan')):
   try:candidate.sample(candidate.matrices[0],invalid)
   except ValueError:pass
   else:raise AssertionError('Invalid fraction accepted')
root=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-model-rectangle-endpoints-20261007');root.mkdir(exist_ok=True)
result=dict(result='PASS_SOURCE_RECTANGLE_ENDPOINT_COMPONENT',rectangle_checks=rectangle_checks,paired_models=models,endpoint_face_checks=checks,max_error=maximum,zero_endpoint_faces=zero_faces,near_endpoint_sign_disagreements=near_disagreements,scope='Original source-model projection determinant endpoints; finite affine-matrix diagnostic interior samples. Not rigid live integration, near-plane coverage, raster output or whole-game fidelity.')
(root/'tests.json').write_text(json.dumps(result,indent=2));(root/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps(result,indent=2))
