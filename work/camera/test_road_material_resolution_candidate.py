import sys,json,struct,types
from pathlib import Path
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json']
exec(compile(Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0],'savedscene','exec'))
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates as baseline
from owned_road_material_resolution_candidate import road_candidates as candidate
import time,statistics,gc,types
try:
 memories=[ClosedSceneMemory(scene.graph,rom) for scene in scenes]
 counts=[]
 for scene,memory in zip(scenes,memories):
  a=baseline(scene.graph,memory);b=candidate(scene.graph,memory)
  assert a==b;counts.append(len(a))
 # Repeated descriptors, complete/missing/conflicting textures and bad dimensions.
 guard_results=[]
 for mode in ('complete','missing_material','unowned_texture','conflict','bad_shift','zero_height'):
  state=bytearray(256);struct.pack_into('<I',state,0,0x08000000)
  body=bytearray(72);struct.pack_into('<I',body,44,16)
  struct.pack_into('<H',body,50,0 if mode=='zero_height' else 2)
  struct.pack_into('<H',body,66,11 if mode=='bad_shift' else 1)
  header=[0]*12;header[3]=1;header[8]=2;header[9]=1;header[10]=1
  materials=struct.pack('<12I',*header)+body+(b'XX' if mode=='conflict' else b'ab')
  if mode=='missing_material':materials=b''
  rec=bytearray(64);struct.pack_into('<H',rec,24,1);struct.pack_into('<H',rec,26,65535)
  graph=types.SimpleNamespace(context=bytes(state),materials=bytes(materials),geometry=bytes(rec)*3,offsets=b'')
  closed=types.SimpleNamespace(graph=graph)
  class Memory:
   def read(self,address,size):
    if mode=='unowned_texture':raise ValueError('unowned')
    assert address==0x08000010 and size==8
    return b'abcdefgh'
  outputs=[]
  for fn in (baseline,candidate):
   try:outputs.append(('result',fn(closed,Memory())))
   except ValueError as error:outputs.append(('error',str(error)))
  assert outputs[0]==outputs[1],mode
  guard_results.append(dict(mode=mode,result=outputs[0][0]))
 samples={'baseline':[],'candidate':[]}
 for scene,memory in zip(scenes,memories):
  for fn in (baseline,candidate):
   for i in range(8):fn(scene.graph,memory)
 enabled=gc.isenabled();gc.disable()
 try:
  for iteration in range(160):
   order=[('baseline',baseline),('candidate',candidate)]
   if iteration%2:order.reverse()
   for label,fn in order:
    began=time.perf_counter_ns()
    for scene,memory in zip(scenes,memories):fn(scene.graph,memory)
    samples[label].append((time.perf_counter_ns()-began)/2e6)
 finally:
  if enabled:gc.enable()
 medians={key:statistics.median(value) for key,value in samples.items()}
 out=dict(result='PASS_ROAD_MATERIAL_RESOLUTION_EQUALITY',candidate_counts=counts,guards=guard_results,median_ms=medians,ratio=medians['candidate']/medians['baseline'],samples_ms=samples,scope='Exact road candidate equality for two saved scenes and six repeated-descriptor guards; alternating same-input extraction benchmark; no live or 4K pixel claim.')
 Path('work/camera/prototype-runs/road-material-resolution-20261009.json').write_text(json.dumps(out,indent=2))
 print(out['result'],counts,medians,out['ratio'],guard_results)
finally:history.close()
