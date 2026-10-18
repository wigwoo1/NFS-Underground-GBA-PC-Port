from pathlib import Path
import runpy,json,struct,math,shutil
import owned_portal_traversal as traversal
from owned_portal_camera_hoist_install_candidate import candidate,original
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010')
rows=[]
try:
 for label,function in (('baseline',original),('hoist',candidate)):
  traversal.traverse=function
  for name in ('test_owned_portal_queue.py','test_owned_portal_limits.py'):
   runpy.run_path('work/camera/'+name,run_name='__main__')
  vertex=bytearray(68);struct.pack_into('<2i',vertex,0,0,1000);struct.pack_into('<H',vertex,48,65535)
  graph={1:(bytes(vertex),0,159),2:(bytes(vertex),0,159)};matrix=(16384,0,0,0,16384,0,0,0,16384,0,0,0);fb=bytearray(64);struct.pack_into('<i',fb,16,1);struct.pack_into('<I',fb,28,80)
  table=(1,)*32768;root=(1,0,239,0,159,0,0)
  result=function(graph,matrix,fb,root,table,descriptor_links={1:2},linked_viewport=(0,239))
  assert len(result)==2 and result[1][0]==2 and result[1][5]==128
  rejects=0
  for kwargs in (dict(capacity=1,descriptor_links={1:2},linked_viewport=(0,239)),dict(descriptor_links={1:2}),dict(descriptor_links={1:3},linked_viewport=(0,239)),dict(sampled_camera=(math.nan,)*12)):
   try:function(graph,matrix,fb,root,table,**kwargs)
   except ValueError:rejects+=1
   else:raise AssertionError('Invalid traversal accepted')
  rows.append(dict(variant=label,linked_regions=len(result),rejections=rejects))
finally:traversal.traverse=original
out=dict(result='PASS_PORTAL_HOIST_DIRECT_CASES',rows=rows,scope='Existing captured queue and six-pair endpoint limits plus linked viewport/capacity/missing target/nonfinite camera checks; hoist remains rejected for measured performance.')
(cp/'portal-hoist-direct-cases.json').write_text(json.dumps(out,indent=2));print(out)
