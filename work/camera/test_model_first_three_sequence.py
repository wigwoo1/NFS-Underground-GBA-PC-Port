"""Measure exact endpoint approach for default and fractional clipping candidate."""
import ctypes as C,json,struct,hashlib
from pathlib import Path
from PIL import Image,ImageChops
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_motion_scene import MotionScene
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_prepared_world_motion import PreparedWorldMotion
from owned_motion_pairs import records
from live_native_batch_candidate import DrawContext
def rigid_camera(pose):
 x,y,z,w=(getattr(pose.rotation,k) for k in ('x','y','z','w'))
 rows=((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),(2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),(2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))
 return (C.c_double*12)(*[rows[r][c] for c in range(3) for r in range(3)],-pose.position.x,-pose.position.y,-pose.position.z)
def compare(actual,endpoint):
 diff=ImageChops.difference(Image.frombytes('RGB',(3840,2160),actual),Image.frombytes('RGB',(3840,2160),endpoint))
 channels=diff.split();maximum=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2])
 hist=maximum.histogram();mae=sum(sum(i*n for i,n in enumerate(c.histogram())) for c in channels)/(3840*2160*3)
 return dict(changed_pixels=3840*2160-hist[0],bbox=diff.getbbox(),mean_absolute_channel_error=mae,max_channel_error=max(i for i,n in enumerate(hist) if n))
p=Path('work/camera');report=json.loads((p/'prototype-runs/owned-native-1791267744113946700.json').read_text());frames=report['wall_diagnostic_frames']
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',(p/'road-correction-reciprocal.bin').read_bytes()[:131072])
from owned_source_model_anchor_candidate import SourceModelAnchors
root=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/model-first-three-sequence-20261007');root.mkdir(exist_ok=True)
history=EndpointRoadPlanner(rom,table);initial=ClosedGraph.decode(Path(frames[0]['graph']).read_bytes());roads,_=history.plan(initial);summaries=[]
try:
 for index,(fa,fb) in enumerate(zip(frames,frames[1:])):
  cp=root/('pair-'+str(index));cp.mkdir(exist_ok=True);checks=[]
  a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b)
  pair=PreparedWorldMotion(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes(),MotionScene(a,sa),MotionScene(b,sb),history,roads,rom)
  next_history=pair.take_next_history();next_roads=pair.endpoint_roads[1]
  plan,_,pa,pb,*_=pair.pair.portal.motion.arguments;rawa=(C.c_int32*12)(*struct.unpack('<12i',plan['camera_older']));rawb=(C.c_int32*12)(*struct.unpack('<12i',plan['camera_newer']));rigida=rigid_camera(pa);rigidb=rigid_camera(pb);model_anchors=SourceModelAnchors(pair.pair.portal.motion)
  try:
   for dll in ('owned-sky-model-first-three-candidate.dll',):
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
        if row['kind']==3 and row['key'] in exact_rows:
         row['blocks'][10]=exact_rows[row['key']]['blocks'][10];row['blocks'][11]=exact_rows[row['key']]['blocks'][11]
        if row['kind']==2 and row['key'] in exact_rows:
         row['blocks'][8]=exact_rows[row['key']]['blocks'][8];row['blocks'][9]=exact_rows[row['key']]['blocks'][9];patched+=1
       assert patched==sum(row['kind']==2 and row['key'] in exact_rows for row in sample_rows)
       header=list(struct.unpack_from('<6I2Q',frame));geometry=b''.join(encode(row) for row in sample_rows);tail=frame[40+header[2]:];header[2]=len(geometry);frame=struct.pack('<6I2Q',*header)+geometry+tail
       models=model_anchors.sample(frame,models,alpha)
       f=C.create_string_buffer(frame);count=len(records(frame)['records'])
       assert d.nf_owned_gpu_draw_scene_clips_anchored(f,len(frame),camera,models,bounds,count,rawa,rawb,rigida,rigidb,alpha)==0;assert d.nf_owned_gpu_read(rgb,len(rgb))==0
       metrics=compare(rgb.raw,exact);checks.append(dict(dll=dll,endpoint=endpoint,epsilon=epsilon,geometry_records=count,matched_wall_materials=patched,**metrics))
       if epsilon==.000000001:Image.frombytes('RGB',(3840,2160),rgb.raw).save(cp/(dll+'-approach-'+str(endpoint)+'.png'))
    finally:assert d.nf_owned_gpu_close()
  finally:pair.close()
  history.close();history=next_history;roads=next_roads
  summary=dict(pair_index=index,older=fa['refresh'],newer=fb['refresh'],checks=checks);summaries.append(summary)
  (root/'tests.json').write_text(json.dumps(dict(result='IN_PROGRESS_SEQUENCE',pairs=summaries,scope='15 consecutive captured complete pairs with retained road history, candidate geometry anchors and matched endpoint texture controls; not live integration or full visibility proof.'),indent=2));print(json.dumps(summary),flush=True)
except Exception as error:
 (root/'failure.json').write_text(json.dumps(dict(pair_index=index,error=repr(error),completed_pairs=len(summaries)),indent=2));raise
finally:
 if 'pair' in locals():pair.close()
 if 'next_history' in locals() and next_history is not history:next_history.close()
 history.close()
(root/'tests.json').write_text(json.dumps(dict(result='MEASURED_COMPLETE_SEQUENCE',completed_pairs=len(summaries),expected_pairs=len(frames)-1,pairs=summaries,scope='Captured consecutive complete pairs with retained road history, geometry anchors and matched endpoint material controls. Pixel differences reported without declaring full fidelity or live integration.'),indent=2))
(root/Path(__file__).name).write_text(Path(__file__).read_text())
