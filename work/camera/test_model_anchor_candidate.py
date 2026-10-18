"""Measure exact endpoint approach for default and fractional clipping candidate."""
import ctypes as C,json,struct,hashlib
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_motion_scene import MotionScene
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_prepared_world_motion import PreparedWorldMotion
from owned_motion_pairs import records
from live_native_batch_candidate import DrawContext
p=Path('work/camera');r=json.loads((p/'prototype-runs/owned-native-1791267744113946700.json').read_text());fa,fb=r['wall_diagnostic_frames'][:2]
a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b)
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',(p/'road-correction-reciprocal.bin').read_bytes()[:131072]);history=EndpointRoadPlanner(rom,table);roads,_=history.plan(a);pair=PreparedWorldMotion(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes(),MotionScene(a,sa),MotionScene(b,sb),history,roads,rom)
from PIL import Image,ImageChops
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/model-anchor-candidate-20261007');cp.mkdir(exist_ok=True)
checks=[]
from owned_source_model_anchor_candidate import SourceModelAnchors
model_anchors=SourceModelAnchors(pair.pair.portal.motion)
plan,_,pa,pb,*_=pair.pair.portal.motion.arguments
rawa=(C.c_int32*12)(*struct.unpack('<12i',plan['camera_older']));rawb=(C.c_int32*12)(*struct.unpack('<12i',plan['camera_newer']))
def rigid_camera(pose):
 x,y,z,w=(getattr(pose.rotation,k) for k in ('x','y','z','w'))
 rows=((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),(2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),(2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))
 return (C.c_double*12)(*[rows[r][c] for c in range(3) for r in range(3)],-pose.position.x,-pose.position.y,-pose.position.z)
rigida=rigid_camera(pa);rigidb=rigid_camera(pb)

def compare(actual,endpoint):
 diff=ImageChops.difference(Image.frombytes('RGB',(3840,2160),actual),Image.frombytes('RGB',(3840,2160),endpoint))
 channels=diff.split();maximum=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2])
 hist=maximum.histogram();mae=sum(sum(i*n for i,n in enumerate(c.histogram())) for c in channels)/(3840*2160*3)
 return dict(changed_pixels=3840*2160-hist[0],bbox=diff.getbbox(),mean_absolute_channel_error=mae,max_channel_error=max(i for i,n in enumerate(hist) if n))
try:
 for dll in ('owned-sky-camera-anchor-candidate.dll',):
  d=C.CDLL(str((p/dll).resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_draw_scene_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_draw_scene_clips_anchored.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_double]
  rgb=C.create_string_buffer(3840*2160*3)
  try:
   for endpoint in (0,1):
    frame,camera,models,bounds,detail=pair.sample(endpoint);f=C.create_string_buffer(frame)
    assert d.nf_owned_gpu_draw(f,len(frame))==0;assert d.nf_owned_gpu_read(rgb,len(rgb))==0;exact=rgb.raw;endpoint_frame=frame
    Image.frombytes('RGB',(3840,2160),exact).save(cp/(dll+'-endpoint-'+str(endpoint)+'.png'))
    for epsilon in (.000000001,):
     alpha=epsilon if endpoint==0 else 1-epsilon
     frame,camera,models,bounds,detail=pair.sample(alpha)
     # Hold endpoint HUD/background/text attachments and their validated identity.
     header=list(struct.unpack_from('<6I2Q',frame));eh=struct.unpack_from('<6I2Q',endpoint_frame);gn=header[2]
     header[1]=eh[1];header[3:6]=eh[3:6];header[7]=eh[7]
     frame=struct.pack('<6I2Q',*header)+frame[40:40+gn]+endpoint_frame[40+eh[2]:]
     from owned_sampled_supplemental_frame import encode
     exact_rows={r['key']:r for r in records(endpoint_frame)['records']};sample_rows=records(frame)['records'];patched=0
     for row in sample_rows:
      if row['kind']==2 and row['key'] in exact_rows:
       row['blocks'][8]=exact_rows[row['key']]['blocks'][8];row['blocks'][9]=exact_rows[row['key']]['blocks'][9];patched+=1
     assert patched>=7
     header=list(struct.unpack_from('<6I2Q',frame));geometry=b''.join(encode(row) for row in sample_rows);tail=frame[40+header[2]:];header[2]=len(geometry);frame=struct.pack('<6I2Q',*header)+geometry+tail
     models=model_anchors.sample(frame,models,alpha)
     f=C.create_string_buffer(frame);count=len(records(frame)['records'])
     assert d.nf_owned_gpu_draw_scene_clips_anchored(f,len(frame),camera,models,bounds,count,rawa,rawb,rigida,rigidb,alpha)==0;assert d.nf_owned_gpu_read(rgb,len(rgb))==0
     metrics=compare(rgb.raw,exact);checks.append(dict(dll=dll,endpoint=endpoint,epsilon=epsilon,geometry_records=count,**metrics))
     if epsilon==.000000001:Image.frombytes('RGB',(3840,2160),rgb.raw).save(cp/(dll+'-approach-'+str(endpoint)+'.png'))
  finally:assert d.nf_owned_gpu_close()
finally:pair.close();history.close()
result=dict(result='MEASURED_ENDPOINT_APPROACH',checks=checks,scope='Actual complete captured pair, exact endpoint native draw compared with sampled pose/visibility/clips approaching each endpoint. Endpoint attachments held fixed, additionally holds each matched endpoint wall indexed texture/palette constant. Source-space endpoint camera and model residual anchoring candidate; held exact wall materials for geometry comparison; no default runtime policy change. Differences must be explained before promotion; not full visual fidelity or live cadence proof.')
(cp/'tests.json').write_text(json.dumps(result,indent=2));(cp/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps(result,indent=2))
