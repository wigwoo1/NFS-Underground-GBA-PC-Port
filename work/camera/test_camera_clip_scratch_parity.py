import sys,json,ctypes as C,struct
from pathlib import Path
from owned_sampled_road_clip import Attributes,clipped_camera_road as reference
from owned_camera_clip_transaction import clipped_camera_road as candidate
from owned_sampled_road_camera import sampled_road_camera
from owned_road_stream_count import surface_stream_count
class Scratch(C.Structure):
 _fields_=[('count',C.c_uint),('addresses',C.c_uint32*512),('depths',C.c_double*512)]
def snapshot(history):return C.string_at(history.scratch,C.sizeof(Scratch))
checks=[]
for report in ('work/camera/prototype-runs/owned-native-1791351241812904600.json','work/camera/prototype-runs/owned-native-1791352541751468500.json'):
 sys.argv=['oracle',report,'0','unused'];ns={};exec(compile(Path('work/camera/capture_fullscene_sample_oracle.py').read_text().split('import time,hashlib')[0],'fixed-setup','exec'),ns)
 try:
  prepared=ns['prepared'];prepared.sample(.5);roads=prepared.roads;context=roads.older.graph.context;near=struct.unpack_from('<i',context,320)[0];base=struct.unpack_from('<I',context,108)[0]
  for key,(raw,attribute_bytes) in roads._decoded_sources.items():
   for alpha in (.1,.5,.9):
    _,pose,_=roads.portal.motion.sample(alpha);camera=sampled_road_camera(raw,roads.ma,roads.mb,roads.portal.endpoints,pose,alpha);count=surface_stream_count(camera,near)
    if count is None:continue
    for affine in (0,1):
     for commit in (False,True):
      a=roads.history.fork();b=roads.history.fork()
      try:
       original=snapshot(a);attrs=Attributes.from_buffer_copy(attribute_bytes);attrs.affine=affine
       args=(camera,attrs,(0,239,0,159),base,count,a.ct)
       result_a=reference(a.d,a.scratch,*args,commit_branch=commit);result_b=candidate(b.d,b.scratch,*args,commit_branch=commit)
       assert result_a==result_b and snapshot(a)==snapshot(b)
       if not commit:assert snapshot(a)==original
       checks.append(dict(descriptor=key[0],alpha=alpha,affine=affine,commit=commit))
      finally:a.close();b.close()
 finally:ns['prepared'].close();ns['history'].close()
assert checks
Path('work/camera/prototype-runs/native-clip-scratch-parity.json').write_text(json.dumps(dict(exact_cases=len(checks),cases=checks,scope='Actual captured sources, affine/nonaffine, commit/noncommit native scratch bytes and clipped outputs exact'),indent=2));print('PASS valid native scratch/output parity',len(checks))
