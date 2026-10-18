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
from owned_source_face_determinant_candidate import SourceFaceDeterminants
root=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/rigid-face-decision-candidate-20261007');root.mkdir(exist_ok=True)
d=C.CDLL(str((p/'owned-sky-camera-anchor-candidate.dll').resolve()));table_c=(C.c_uint32*32768)(*table)
history=EndpointRoadPlanner(rom,table);initial=ClosedGraph.decode(Path(frames[0]['graph']).read_bytes());roads,_=history.plan(initial);checks=[]
try:
 for index,(fa,fb) in enumerate(zip(frames,frames[1:])):
  a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b)
  pair=PreparedWorldMotion(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes(),MotionScene(a,sa),MotionScene(b,sb),history,roads,rom);next_history=pair.take_next_history();next_roads=pair.endpoint_roads[1]
  try:
   endpoints=[{r['key']:r for r in records(pair.sample(i)[0])['records'] if r['kind']==3} for i in (0,1)]
   classifiers={k:SourceFaceDeterminants(endpoints[0][k],endpoints[1][k],d,table_c) for k in endpoints[0].keys()&endpoints[1].keys()};anchors=SourceModelAnchors(pair.pair.portal.motion)
   for alpha in (1e-9,1e-6,.001,.25,.5,.75,.999,1-1e-6,1-1e-9):
    frame,camera,models,bounds,detail=pair.sample(alpha);models=anchors.sample(frame,models,alpha)
    for position,row in enumerate(records(frame)['records']):
     if row['kind']!=3:continue
     classifier=classifiers[row['key']];matrix=tuple(models[position*12:position*12+12]);values=classifier.sample(matrix,alpha);decisions=classifier.decisions(matrix,alpha)
     endpoint=0 if alpha<=.001 else 1 if alpha>=.999 else None
     disagree=None if endpoint is None else sum(x!=(y>=0) for x,y in zip(decisions,classifier.exact[endpoint]))
     checks.append(dict(pair=index,alpha=alpha,faces=len(values),visible=sum(decisions),endpoint=endpoint,endpoint_disagreements=disagree,minimum_threshold_distance=min(abs(v+.5) for v in values)))
  finally:pair.close()
  history.close();history=next_history;roads=next_roads
finally:
 history.close()
 if 'next_history' in locals() and next_history is not history:next_history.close()
near=[x for x in checks if x['alpha'] in (1e-9,1-1e-9)];result=dict(result='MEASURED_RIGID_FACE_DECISION_POLICY',pairs=len(frames)-1,samples=len(checks),near_endpoint_face_checks=sum(x['faces'] for x in near),near_endpoint_disagreements=sum(x['endpoint_disagreements'] for x in near),checks=checks,scope='Actual rigid model samples plus source-matrix anchors, determinant residual and midpoint integer decision-cell extension. No GPU classification/near-plane/rectangle proof or default promotion.')
(root/'tests.json').write_text(json.dumps(result,indent=2));(root/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
