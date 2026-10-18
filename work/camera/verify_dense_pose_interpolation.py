"""Independent endpoint interpolation; separate visibility poses from presentation camera."""
import hashlib,json,math,struct,sys
from pathlib import Path
import numpy as np
manifest=Path(sys.argv[1]);session=json.loads(manifest.read_text(encoding='utf-8-sig'));prefix=session['prefix'];source_path=Path(prefix+'-dense-source-identity-verification.json');sources=json.loads(source_path.read_text())
def parse(data):
 sections={t:data[o:o+n] for t,o,n in (struct.unpack_from('<3I',data,32+j*12) for j in range(5))};m=sections[1];count=struct.unpack_from('<I',m,4)[0] if m[:4]==b'NML1' else 1;world=struct.unpack_from('<I',sections[2],4)[0];result={}
 for j in range(count):
  at=struct.unpack_from('<I',m,8+j*8)[0] if m[:4]==b'NML1' else 0;assert m[at:at+4]==b'NFM2';identity=struct.unpack_from('<5I',sections[5],8+(world+j)*20);result[identity]=(np.array(struct.unpack_from('<7d',m,at+48)),np.array(struct.unpack_from('<7d',m,at+104)))
 return result
def interpolate(a,b,t):
 qa=a[3:]/np.linalg.norm(a[3:]);qb=b[3:]/np.linalg.norm(b[3:]);d=float(np.dot(qa,qb))
 if d<0:qb=-qb;d=-d
 d=min(1,d);wa,wb=1-t,t
 if d<.9995:theta=math.acos(d);wa=math.sin((1-t)*theta)/math.sin(theta);wb=math.sin(t*theta)/math.sin(theta)
 q=qa*wa+qb*wb;q/=np.linalg.norm(q);return np.r_[(1-t)*a[:3]+t*b[:3],q]
def errors(actual,expected):return dict(position=float(np.linalg.norm(actual[:3]-expected[:3])),rotation_degrees=math.degrees(2*math.acos(min(1,abs(float(np.dot(actual[3:]/np.linalg.norm(actual[3:]),expected[3:])))))))
def decode_matrix(matrix):
 columns=np.array(matrix[:9],dtype=float).reshape(3,3).T/16384
 x=columns[:,0];x/=np.linalg.norm(x);y=columns[:,1]-x*np.dot(x,columns[:,1]);y/=np.linalg.norm(y);z=np.cross(x,y);assert np.dot(z,columns[:,2])>0
 r=np.column_stack((x,y,z));a,b,c=r[0,0],r[1,1],r[2,2]
 k=np.array([[a-b-c,r[1,0]+r[0,1],r[2,0]+r[0,2],r[2,1]-r[1,2]],[r[1,0]+r[0,1],b-a-c,r[2,1]+r[1,2],r[0,2]-r[2,0]],[r[2,0]+r[0,2],r[2,1]+r[1,2],c-a-b,r[1,0]-r[0,1]],[r[2,1]-r[1,2],r[0,2]-r[2,0],r[1,0]-r[0,1],a+b+c]])
 _,vectors=np.linalg.eigh(k);return vectors[:,-1]
def round_away(values):return np.copysign(np.floor(np.abs(values)+.5),values)
def quantize_pose(pose):
 x,y,z,w=pose[3:];r=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
 matrix=round_away(r.T.reshape(9)*16384);return np.r_[round_away(pose[:3]*256)/256,decode_matrix(matrix)]
endpoints={}
for row in sources['original_endpoints']:
 data=Path(row['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256'];endpoints[row['identity'][3]]=parse(data)
raw_poses={};visible_raw_checks=0
for row in sources.get('original_object_pose_inputs',[]):
 record=bytes.fromhex(row['record_hex']);assert len(record)==164 and hashlib.sha256(record).hexdigest()==row['record_sha256']
 q=decode_matrix(row['world_rotation']);pose=np.r_[np.array(struct.unpack_from('<3i',record,12))/256,q];key=tuple(row['identity']);end=row['endpoint_refresh'];raw_poses[end,key]=pose
 if key in endpoints[end]:
  visible=endpoints[end][key][1];assert np.array_equal(visible[:3],pose[:3]);assert min(np.linalg.norm(visible[3:]-q),np.linalg.norm(visible[3:]+q))<1e-10;visible_raw_checks+=1
checks=[]
for i in range(1,session['dense_frames']+1):
 base=Path(prefix+f'-dense-{i:02d}');meta=json.loads(Path(str(base)+'-native-source.json').read_text());data=Path(str(base)+'-native-scene.bin').read_bytes();native=parse(data);left,right=[endpoints[e] for e in meta['source_refreshes']]
 # Exact alpha, not JSON-rounded diagnostic alpha.
 ids_offset=struct.unpack_from('<I',data,84)[0];ids_count=struct.unpack_from('<I',data,ids_offset+4)[0];alpha=struct.unpack_from('<d',data,ids_offset+8+ids_count*20+8)[0]
 ca=next(iter(left.values()))[0];cb=next(iter(right.values()))[0];assert all(np.array_equal(v[0],ca) for v in left.values()) and all(np.array_equal(v[0],cb) for v in right.values());effective=interpolate(ca,cb,alpha);model_checks=[];missing=[]
 for key,(camera,obj) in native.items():
  ends=meta['source_refreshes'];a=left[key][1] if key in left else raw_poses.get((ends[0],key));b=right[key][1] if key in right else raw_poses.get((ends[1],key))
  if a is None or b is None:missing.append(list(key));continue
  recovered=key not in left or key not in right;expected=interpolate(a,b,alpha)
  # nf_object_pose_sample rounds each position component to 1/256 world unit.
  assert np.max(np.abs(obj[:3]-expected[:3]))<=1/512+1e-8
  rounded=quantize_pose(expected);assert np.array_equal(obj[:3],rounded[:3]);residual=min(np.linalg.norm(obj[3:]-rounded[3:]),np.linalg.norm(obj[3:]+rounded[3:]));assert residual<1e-10
  model_checks.append(dict(identity=list(key),errors=errors(obj,expected),position_within_source_rounding_bound=True,recovered_retained_original_pose=recovered,exact_rounded_position=True,quantized_rotation_quaternion_residual=float(residual)))
 checks.append(dict(index=i,target=meta['target'],alpha=alpha,packet_sha256=hashlib.sha256(data).hexdigest(),effective_presentation_camera=effective.tolist(),packet_visibility_camera_errors=errors(next(iter(native.values()))[0],effective),models=model_checks,models_missing_visible_endpoint=missing))
out=Path(prefix+'-dense-pose-interpolation-verification.json');out.write_text(json.dumps(dict(result='MEASURED',source_report_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),visible_endpoint_raw_pose_checks=visible_raw_checks,recovered_observations=sum(m['recovered_retained_original_pose'] for c in checks for m in c['models']),checks=checks,scope='Independent linear position and shortest-arc quaternion interpolation from hash-validated original visible endpoint poses or retained original object records/world rotation matrices. Raw matrix decoder independently uses Gram-Schmidt and symmetric eigen quaternion conversion, cross-checked against visible endpoint poses. Effective presentation camera follows retained-camera override; packet camera is rounded visibility input. Any missing raw endpoints stay explicit. Model fixed-point position and 1/16384 rotation matrix conversion are independently reproduced and checked; raster/scanout/full-game smoothness remain separate.'),indent=2))
print(json.dumps(dict(frames=len(checks),camera_visibility_position_error_max=max(c['packet_visibility_camera_errors']['position'] for c in checks),model_position_error_max=max(m['errors']['position'] for c in checks for m in c['models']),model_rotation_error_max_degrees=max(m['errors']['rotation_degrees'] for c in checks for m in c['models']),models_missing_endpoint=sum(len(c['models_missing_visible_endpoint']) for c in checks))))

