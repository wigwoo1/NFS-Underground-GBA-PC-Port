"""Independent quaternion/matrix projection audit of immutable dense scene geometry."""
import ctypes as C,hashlib,json,math,struct,sys
from pathlib import Path
import numpy as np
manifest=Path(sys.argv[1]); session=json.loads(manifest.read_text(encoding='utf-8-sig')); prefix=session['prefix']; previous=None; steps=[]; frames=[]
pose_path=Path(prefix+'-dense-pose-interpolation-verification.json');assert pose_path.exists(),'Generate endpoint camera reference before auditing live projected geometry'
pose_report=json.loads(pose_path.read_text());effective_cameras={c['index']:c for c in pose_report['checks']}
bridge=Path(__file__).resolve().parent/'visibility-probe-wide.dll';dll=C.CDLL(str(bridge));sample=dll.nf_rigid_scene_sample;sample.argtypes=[C.c_void_p]*4+[C.c_double,C.c_void_p,C.c_uint,C.c_void_p];checked_vertices=0;maximum_transform_error=0
def rotation(q):
 q=np.asarray(q); assert np.isfinite(q).all() and abs(np.linalg.norm(q)-1)<1e-6
 x,y,z,w=q; return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def angle(a,b):return math.degrees(2*math.acos(min(1,abs(float(np.dot(a,b))))))
def project(vertices,camera,obj,projection):
 global checked_vertices,maximum_transform_error
 # Packet camera quaternion already rotates world-relative coordinates into
 # camera space; it is not a camera-to-world orientation to invert.
 points=(vertices@rotation(obj[3:]).T+obj[:3]-camera[:3])@rotation(camera[3:]).T; valid=points[:,2]>=1
 output=np.empty_like(vertices);camera=np.ascontiguousarray(camera,dtype=np.float64);obj=np.ascontiguousarray(obj,dtype=np.float64);vertices=np.ascontiguousarray(vertices,dtype=np.float64)
 assert sample(camera.ctypes.data,camera.ctypes.data,obj.ctypes.data,obj.ctypes.data,0,vertices.ctypes.data,len(vertices),output.ctypes.data)
 error=float(np.max(np.abs(points-output))); assert error<1e-7;maximum_transform_error=max(maximum_transform_error,error);checked_vertices+=len(vertices)
 pixels=np.empty((len(points),2));pixels[:]=np.nan;pixels[valid]=np.asarray(projection[:2])+projection[2]*points[valid,:2]/points[valid,2,None]
 return pixels,valid,points[:,2]
def stats(values):return dict(count=len(values),median=float(np.median(values)),p99=float(np.percentile(values,99)),maximum=float(np.max(values))) if len(values) else None
for index in range(1,session['dense_frames']+1):
 base=Path(prefix+f'-dense-{index:02d}'); data=Path(str(base)+'-native-scene.bin').read_bytes();meta=json.loads(Path(str(base)+'-native-source.json').read_text());sections={t:data[o:o+n] for t,o,n in (struct.unpack_from('<3I',data,32+j*12) for j in range(5))}
 reference=effective_cameras[index];assert reference['packet_sha256']==hashlib.sha256(data).hexdigest();effective_camera=np.array(reference['effective_presentation_camera'])
 trailer=8+20*struct.unpack_from('<I',sections[5],4)[0]; assert sections[5][trailer:trailer+4]==b'NFB2'
 def portal(ordinal):return list(struct.unpack_from('<4H',sections[5],trailer+16+ordinal*8))
 models=sections[1]; assert models[:4] in (b'NML1',b'NFM2'); count=struct.unpack_from('<I',models,4)[0] if models[:4]==b'NML1' else 1; world_count=struct.unpack_from('<I',sections[2],4)[0]; objects={}; cameras=[]; projections=[]
 for j in range(count):
  offset,size=struct.unpack_from('<2I',models,8+j*8) if models[:4]==b'NML1' else (0,len(models)); model=models[offset:offset+size];assert model[:4]==b'NFM2'
  camera=effective_camera;obj=np.array(struct.unpack_from('<7d',model,104));projection=struct.unpack_from('<3d',model,24);n=struct.unpack_from('<I',model,4)[0];raw=model[160:160+n*24];vertices=np.frombuffer(raw,dtype='<f8').reshape(n,3)
  identity=struct.unpack_from('<5I',sections[5],8+(world_count+j)*20); assert identity not in objects
  pixels,valid,depth=project(vertices,camera,obj,projection);objects[identity]=dict(depth=depth,near=1,portal=portal(world_count+j),ordinal=j,pose=obj,vertices_sha256=hashlib.sha256(raw).hexdigest(),pixels=pixels,valid=valid);cameras.append(camera);projections.append(projection)
 assert all(np.array_equal(c,cameras[0]) for c in cameras);camera=cameras[0];rotation(camera[3:])
 assert all(p==projections[0] for p in projections)
 world={};at=8;occurrences={}
 for j in range(world_count):
  n,w,h=struct.unpack_from('<3I',sections[2],at);raw=sections[2][at+12:at+12+n*24];vertices=np.frombuffer(raw,dtype='<f8').reshape(n,3);identity=struct.unpack_from('<5I',sections[5],8+j*20);occurrence=occurrences.get(identity,0);occurrences[identity]=occurrence+1
  key=identity+(occurrence,); pixels,valid,depth=project(vertices,camera,np.array([0,0,0,0,0,0,1]),projection);world[key]=dict(depth=depth,near=64,portal=portal(j),ordinal=j,vertices_sha256=hashlib.sha256(raw).hexdigest(),pixels=pixels,valid=valid);at+=12+n*40+w*h*4
 clipping=[]
 for kind,commands in [('model',objects),('world',world)]:
  for key,c in commands.items():
   front=c['depth']>=c['near'];clipping.append(dict(kind=kind,identity=list(key),ordinal=c['ordinal'],near_depth=c['near'],depth_min=float(c['depth'].min()),depth_max=float(c['depth'].max()),front_vertices=int(front.sum()),vertices=len(front),straddles_near=bool(front.any() and not front.all()),portal=c['portal']))
 frame=dict(clipping=clipping,index=index,target=meta['target'],packet_sha256=hashlib.sha256(data).hexdigest(),models=count,world_surfaces=world_count)
 if previous:
  oldframe,oldcamera,oldobjects,oldworld=previous; clipping_events=[]
  for kind,new,old in [('model',objects,oldobjects),('world',world,oldworld)]:
   for key in sorted(new.keys()&old.keys()):
    a,b=old[key],new[key]
    if a['vertices_sha256']!=b['vertices_sha256']:continue
    crossing=np.flatnonzero((a['depth']>=a['near'])!=(b['depth']>=b['near'])).tolist();portal_changed=a['portal']!=b['portal']
    if crossing or portal_changed:clipping_events.append(dict(kind=kind,identity=list(key),from_ordinal=a['ordinal'],to_ordinal=b['ordinal'],near_crossing_vertices=crossing,portal_changed=portal_changed,from_portal=a['portal'],to_portal=b['portal']))
  model_steps=[];world_steps=[];changed_geometry=[]
  for key in sorted(objects.keys()&oldobjects.keys()):
   a,b=oldobjects[key],objects[key];entry=dict(identity=list(key),rotation_degrees=angle(a['pose'][3:],b['pose'][3:]))
   if a['vertices_sha256']==b['vertices_sha256']:
    valid=a['valid']&b['valid']; entry['projected_vertex_step_gba_pixels']=stats(np.linalg.norm(b['pixels'][valid]-a['pixels'][valid],axis=1))
   else:changed_geometry.append(list(key))
   model_steps.append(entry)
  for key in sorted(world.keys()&oldworld.keys()):
   a,b=oldworld[key],world[key]
   if a['vertices_sha256']!=b['vertices_sha256']:changed_geometry.append(list(key));continue
   valid=a['valid']&b['valid']; world_steps.extend(np.linalg.norm(b['pixels'][valid]-a['pixels'][valid],axis=1).tolist())
  steps.append(dict(clipping_events=clipping_events,from_index=oldframe['index'],to_index=index,camera_rotation_degrees=angle(oldcamera[3:],camera[3:]),models=model_steps,world_projected_vertex_step_gba_pixels=stats(world_steps),geometry_changed_identities=changed_geometry))
 previous=(frame,camera,objects,world);frames.append(frame)
assert len(steps)==session['dense_frames']-1
out=Path(prefix+'-dense-projected-motion-audit.json');out.write_text(json.dumps(dict(result='AUDITED',presentation_camera_reference_sha256=hashlib.sha256(pose_path.read_bytes()).hexdigest(),bridge_sha256=hashlib.sha256(bridge.read_bytes()).hexdigest(),checked_transform_vertices=checked_vertices,maximum_transform_error=maximum_transform_error,frames=frames,steps=steps,smooth_60fps_verified=False,scope='Independent quaternion rotation matrices and continuous perspective projection of every packet model/world vertex using effective continuous presentation camera, checked against actual native rigid transform API. Supersedes earlier rounded packet-camera projection audits. Vertex comparisons require exact geometry hashes and source identity plus occurrence joins. Classifies near-plane masks at renderer thresholds (models1, world64) and owned NFB2 portal changes for unchanged persistent geometry. Projection statistics include offscreen points and use positive depth>=1; large offscreen steps are not visual discontinuity evidence. No screen-polygon matching, raster parity or scanout proof.'),indent=2))
print(json.dumps(dict(report=str(out),pairs=len(steps),near_crossing_events=sum(bool(e['near_crossing_vertices']) for st in steps for e in st['clipping_events']),portal_change_events=sum(e['portal_changed'] for st in steps for e in st['clipping_events']),straddling_commands=sum(c['straddles_near'] for f in frames for c in f['clipping']),camera_rotation_max_degrees=max(s['camera_rotation_degrees'] for s in steps),geometry_changed=sum(len(s['geometry_changed_identities']) for s in steps),model_rotation_max_degrees=max(m['rotation_degrees'] for s in steps for m in s['models']))))
