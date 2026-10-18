import json,time,statistics,tracemalloc
from pathlib import Path
from owned_scene_single_join_pack_candidate import original,pack
from owned_scene_process_transport import unpack
ns={};exec(Path('work/camera/profile_complete_scene_unpack_candidate.py').read_text().split('for iteration in range(8):')[0],ns);env=ns['ns']['envs'][0];inputs=list(zip(env['frames'],env['scenes']));rom=ns['rom'];expected=[original(*x) for x in inputs];cost={label:[] for label in ('baseline','candidate')};combined={label:[] for label in cost}
for i in range(60):
 for label in (('baseline','candidate') if i%2==0 else ('candidate','baseline')):
  fn=original if label=='baseline' else pack;begin=time.perf_counter_ns();actual=[fn(*x) for x in inputs];end=time.perf_counter_ns();decoded=[unpack(x,rom) for x in actual];finished=time.perf_counter_ns()
  assert actual==expected and [original(*x) for x in decoded]==expected
  cost[label].append((end-begin)/1e6);combined[label].append((finished-begin)/1e6)
allocation=[]
for label in ('baseline','candidate','candidate','baseline'):
 fn=original if label=='baseline' else pack;tracemalloc.start();actual=[fn(*x) for x in inputs];current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();allocation.append(dict(label=label,current=current,peak=peak));del actual
out=dict(result='PASS_SINGLE_JOIN_FULL_SCENE_WIRE_PARITY',rounds=60,pack_medians={k:statistics.median(v) for k,v in cost.items()},pack_unpack_medians={k:statistics.median(v) for k,v in combined.items()},pack_ms=cost,pack_unpack_ms=combined,allocations=allocation,scope='Two actual complete captured endpoints; original full wire bytes and decoded scene re-encoding exact. Timing includes scene.match; no shared-worker/live/native4K proof.')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/scene-single-join-pack-20261010');cp.mkdir(exist_ok=True);(cp/'component.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ('pack_ms','pack_unpack_ms')},indent=2))
