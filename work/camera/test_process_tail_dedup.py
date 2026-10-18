import runpy,json
from pathlib import Path
from owned_process_preparation_service import encode_samples,ProcessSamples
from test_scene_process_transport import digest
v=runpy.run_path('work/camera/test_external_fullscene_transition.py');original=sent=0;checks=0
for start in range(0,101,8):
 samples={i/100:v['samples'][i] for i in range(start,min(start+8,101))};packet=encode_samples(samples);decoded=ProcessSamples(packet)
 try:
  for alpha,value in samples.items():assert digest(decoded.sample(alpha))==digest(value);checks+=1
 finally:decoded.close()
 original+=packet['original_bytes'];sent+=packet['transferred_bytes']
result=dict(exact_complete_samples=checks,original_bytes=original,transferred_bytes=sent,reduction_fraction=1-sent/original,scope='lossless output transport component, not live timing')
Path('work/camera/prototype-runs/process-tail-dedup.json').write_text(json.dumps(result,indent=2));print(result)
