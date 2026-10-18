"""Alternating same-scene dispatcher comparison; no live cadence claim."""
import sys,time,json,statistics
from pathlib import Path
import owned_sampled_road_sequence as roads
from owned_sampled_road_clip import clipped_camera_road as original
from owned_camera_road_dispatch import clipped_camera_road as fused
from test_scene_process_transport import digest
report=sys.argv[1] if len(sys.argv)>1 else 'work/camera/prototype-runs/owned-native-1791352541751468500.json'
start=sys.argv[2] if len(sys.argv)>2 else '0'
checkpoint=sys.argv[3] if len(sys.argv)>3 else 'fused-road-controlled-20261007'
sys.argv=['setup',report,start,'unused']
ns={};exec(compile(Path('work/camera/capture_fullscene_sample_oracle.py').read_text().split('import time,hashlib')[0],'setup','exec'),ns)
p=ns['prepared'];results=[];reference={}
try:
 for turn in range(24):
  order=(('original',original),('fused',fused)) if turn%2==0 else (('fused',fused),('original',original))
  for name,fn in order:
   roads.clipped_camera_road=fn
   for alpha in (.25,.5,.75):
    cpu=time.thread_time_ns();begin=time.perf_counter_ns();value=p.sample(alpha);wall=time.perf_counter_ns()-begin;cpu=time.thread_time_ns()-cpu
    key=digest(value)
    if alpha in reference:assert reference[alpha]==key
    else:reference[alpha]=key
    stage=next(s for s in p.pair._last_sample_stages if s['name']=='sampled_roads')
    if turn>=4:results.append(dict(turn=turn,dispatcher=name,alpha=alpha,wall_ns=wall,cpu_ns=cpu,road_wall_ns=stage['wall_ns'],road_cycles=stage['thread_cycles'],assembly_stages=p.pair._last_sample_stages))
finally:
 roads.clipped_camera_road=original;p.close();ns['history'].close()
summary={}
for name in ('original','fused'):
 rows=[r for r in results if r['dispatcher']==name]
 summary[name]={key:statistics.median(r[key] for r in rows) for key in ('wall_ns','cpu_ns','road_wall_ns','road_cycles')}
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints')/checkpoint;cp.mkdir(exist_ok=True)
(cp/'comparison.json').write_text(json.dumps(dict(result='PASS_EXACT_SCENE_PARITY',samples=results,median=summary,scope='Alternating dispatchers same warmed captured interval/three alphas, 20measured rounds; component timing not live producer/contention/scanout'),indent=2))
(cp/'compare_fused_road_dispatch.py').write_text(Path(__file__).read_text());print(json.dumps(summary))
