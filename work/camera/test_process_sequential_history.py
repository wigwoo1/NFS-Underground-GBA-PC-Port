import json,sys,ctypes as C
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_model_builder_inputs import OwnedModelBuilders
from owned_model_sources import OwnedModelSources
from owned_motion_scene import MotionScene
from owned_process_preparation_service import ProcessPreparationService
from owned_world_preparation_service import WorldPreparationService
from test_scene_process_transport import digest
if __name__=='__main__':
 rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();r=json.loads(Path(sys.argv[1]).read_text());pairs=[]
 for c in r['model_scene_captures']:
  g=ClosedGraph.decode(Path(c['graph']).read_bytes());s=MotionScene(g,ClosedSupplements.decode(Path(c['supplements']).read_bytes(),g,rom),OwnedModelBuilders(Path(c['builders']).read_bytes()),OwnedModelSources.decode(Path(c['current-sources']).read_bytes(),g));pairs.append((Path(c['frame']).read_bytes(),s))
 gpu=None;gpu_checks=0
 if '--gpu' in sys.argv:
  gpu=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));gpu.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];gpu.nf_owned_gpu_draw_scene_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];gpu.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3)
 process=ProcessPreparationService(rom,2,shared_output="--shared" in sys.argv);reference=WorldPreparationService(rom,2);checks=0
 try:
  for older,newer in zip(pairs,pairs[1:]):
   a=reference.take(reference.submit(older,newer,(0,.5,1),timeout=5));b=process.take(process.submit(older,newer,(0,.5,1),timeout=5))
   try:
    for alpha in (0,.5,1):
     sample=b.sample(alpha);assert digest(a.sample(alpha))==digest(sample);checks+=1
     if gpu is not None:
      frame,camera,models,bounds,detail=sample
      assert (gpu.nf_owned_gpu_draw(frame,len(frame)) if alpha in (0,1) else gpu.nf_owned_gpu_draw_scene_clips(frame,len(frame),camera,models,bounds,detail['geometry_records']))==0
      assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0;gpu_checks+=1
   finally:a.close();b.close()
  reused=sum(x['input_reused'] for x in process.stage_samples);assert reused==len(pairs)-2
  result=dict(native4k_readbacks=gpu_checks,exact_samples=checks,sequential_intervals=len(pairs)-1,reused_inputs=reused,stage_samples=process.stage_samples)
 finally:
  reference.close();process.close()
  if gpu is not None:assert gpu.nf_owned_gpu_close()
 Path('work/camera/prototype-runs/process-sequential-shared-history.json' if "--shared" in sys.argv else 'process-sequential-history.json').write_text(json.dumps(result,indent=2));print(dict(exact_samples=checks,reused_inputs=reused))
