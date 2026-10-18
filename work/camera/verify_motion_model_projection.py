from pathlib import Path
import ctypes as C,struct,json,hashlib
p=Path('work/camera');snap=json.loads((p/'motion-model-snapshots.json').read_text());table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes())
f=C.CDLL(str((p/'native_model.dll').resolve())).nfs_model_project;f.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint32,C.c_int32,C.c_int32,C.c_void_p,C.c_void_p]
checks=[];models=[]
for scene in snap['scenes']:
 for model in scene['models']:
  source=struct.pack('<'+'h'*len(model['vertices'])*3,*[v for xyz in model['vertices'] for v in xyz]);matrix=bytes.fromhex(model['transform_hex']);context=bytes.fromhex(model['context_hex']);fb=bytes.fromhex(model['framebuffer_descriptor_hex']);scale=struct.unpack_from('<I',context,64)[0];x,y=struct.unpack_from('<2h',fb,8);out=C.create_string_buffer(len(model['vertices'])*4)
  eligible=f(matrix,source,len(model['vertices']),scale,x,y,table,out);expected=Path(model['source_projected_oracle']['path']).read_bytes();assert hashlib.sha256(expected).hexdigest()==model['source_projected_oracle']['sha256']
  actual=out.raw;checks.append(dict(event=model['event'],eligible=eligible,vertices=len(model['vertices']),exact=bool(eligible and actual==expected)))
  points=[list(struct.unpack_from('<2h',actual,i*4)) for i in range(len(model['vertices']))];faces=[]
  for i,face in enumerate(model['faces']):
   ring=[points[v] for v in face['vertices']];a,b,c=ring[:3];det=(b[1]-a[1])*(c[0]-a[0])-(c[1]-a[1])*(b[0]-a[0]);det=((det+0x80000000)&0xffffffff)-0x80000000
   faces.append(dict(face=i,ring=ring,uv_indices=face['uv'],first_three_determinant=det,original_backface_skip=det<0))
  models.append(dict(event=model['event'],begin=scene['begin'],end=scene['end'],points=points,faces=faces,eligible=eligible))
r=dict(result='PASS_NATIVE_MOTION_MODEL_PROJECTION' if all(c['exact'] for c in checks) else 'MODEL_PROJECTION_DIFFERENCE',checks=checks,vertices=sum(c['vertices'] for c in checks),scope='Raw signed local vertices and captured object/camera transform to native integer projection; complete projected scratch checked independently. Matrix composition still captured input; face raster writes and fullscene timing unverified.')
(p/'motion-model-projection-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');(p/'native-motion-model-faces.json').write_text(json.dumps(dict(models=models,scope='Native projected source-topology face rings; backface metadata not yet checked against actual draw calls.'),indent=2),encoding='utf-8');print(r['result'],r['vertices']);print([c for c in checks if not c['exact']])
