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
import json,struct,hashlib,ctypes as C
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_graph_packet import GraphPacket
from owned_closed_supplements import ClosedSupplements
from owned_model_builder_inputs import OwnedModelBuilders
from owned_model_sources import OwnedModelSources
from owned_motion_scene import MotionScene
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_motion_pairs import records
root=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-source-context-20261007/failure-snapshot');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();frames=[];scenes=[]
for label in ('older','newer'):
 frames.append((root/(label+'.frame.bin')).read_bytes());g=ClosedGraph(struct.unpack_from('<Q',frames[-1],24)[0],struct.unpack_from('<I',frames[-1],4)[0],GraphPacket.decode((root/(label+'.graph.bin')).read_bytes()),*((root/(label+'.'+field+'.bin')).read_bytes() for field in ('objects','callbacks','associations')));scenes.append(MotionScene(g,ClosedSupplements.decode((root/(label+'.supplements.bin')).read_bytes(),g,rom),OwnedModelBuilders((root/(label+'.builders.bin')).read_bytes()),OwnedModelSources.decode((root/(label+'.current-sources.bin')).read_bytes(),g)))


import sys
kind=int(sys.argv[1]);assert kind in (1,2,3)
def filter_scene(frame,models=None,bounds=None):
 from owned_sampled_supplemental_frame import encode
 rows=records(frame)['records'];indices=[i for i,r in enumerate(rows) if r['kind']==kind]
 header=list(struct.unpack_from('<6I2Q',frame));tail=frame[40+header[2]:];geom=b''.join(encode(rows[i]) for i in indices);header[2]=len(geom)
 f=struct.pack('<6I2Q',*header)+geom+tail
 m=None if models is None else (C.c_double*(len(indices)*12))(*(models[i*12+j] for i in indices for j in range(12)))
 b=None if bounds is None else (C.c_double*(len(indices)*4))(*(bounds[i*4+j] for i in indices for j in range(4)))
 return f,m,b

p=Path('work/camera');table=struct.unpack('<32768I',(p/'road-correction-reciprocal.bin').read_bytes()[:131072]);history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);pair=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
from owned_source_native_depth_rectangle_candidate import OwnedProjectionTable
from owned_source_presentation_batch_candidate import prepare_source_models
from owned_source_face_mask_candidate import build_source_face_mask
from owned_source_draw_context_candidate import OwnedSourceDraw
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-wall-source-material-kind-'+str(kind)+'-20261007');cp.mkdir(exist_ok=True);checks=[]
dll='owned-sky-source-context-candidate.dll';d=C.CDLL(str((p/dll).resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_source_context_callback.argtypes=[C.c_void_p]
model_anchors,classifiers=prepare_source_models(pair,d,OwnedProjectionTable(table))
plan,_,pa,pb,*_=pair.pair.portal.motion.arguments;rawa=(C.c_int32*12)(*struct.unpack('<12i',plan['camera_older']));rawb=(C.c_int32*12)(*struct.unpack('<12i',plan['camera_newer']));rigida=rigid_camera(pa);rigidb=rigid_camera(pb)
assert d.nf_owned_gpu_window(0)==0;rgb=C.create_string_buffer(3840*2160*3)
try:
 for endpoint in (0,1):
  frame,camera,models,bounds,detail=pair.sample(endpoint);frame,_,_=filter_scene(frame);f=C.create_string_buffer(frame)
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
    if row['kind']==2:
     matches=[e for e in exact_rows.values() if e['kind']==2 and e['blocks'][0]==row['blocks'][0] and e['blocks'][1]==row['blocks'][1]]
     if matches:
      assert len(matches)==1,'Ambiguous source wall'
      row['blocks'][8]=matches[0]['blocks'][8];row['blocks'][9]=matches[0]['blocks'][9];patched+=1
   assert patched<=len(exact_rows)
   header=list(struct.unpack_from('<6I2Q',frame));geometry=b''.join(encode(row) for row in sample_rows);tail=frame[40+header[2]:];header[2]=len(geometry);frame=struct.pack('<6I2Q',*header)+geometry+tail
   models=model_anchors.sample(frame,models,alpha)
   frame,models,bounds=filter_scene(frame,models,bounds)
   f=C.create_string_buffer(frame);count=len(records(frame)['records'])
   offsets_c,mask_c,total,mask_detail=build_source_face_mask(frame,models,bounds,alpha,classifiers)
   owned=OwnedSourceDraw(frame,camera,models,bounds,count,rawa,rawb,rigida,rigidb,alpha,offsets_c,mask_c,total)
   assert d.nf_owned_gpu_source_context_callback(C.byref(owned.context))==0;assert d.nf_owned_gpu_read(rgb,len(rgb))==0
   metrics=compare(rgb.raw,exact);checks.append(dict(dll=dll,endpoint=endpoint,epsilon=epsilon,geometry_records=count,matched_wall_materials=patched,**mask_detail,**metrics))
   if epsilon==.000000001:Image.frombytes('RGB',(3840,2160),rgb.raw).save(cp/(dll+'-approach-'+str(endpoint)+'.png'))
finally:
 assert d.nf_owned_gpu_close();pair.close();history.close()
result=dict(result='MEASURED_PORTAL_EXIT_ENDPOINTS',checks=checks,scope='Diagnostic source vertices+offsets unique identity; held endpoint textures/palette only. Seven older/five newer matched. Unmatched walls retained. Not production material interpolation or complete fidelity proof.')
(cp/'tests.json').write_text(json.dumps(result,indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(result,indent=2))
