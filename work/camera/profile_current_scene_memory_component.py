import sys,json,cProfile,statistics,time
from pathlib import Path
sys.argv=['fixture','work/camera/prototype-runs/child-scene-1791637661169682300']
setup=Path('work/camera/test_geometry_process_codec_component.py').read_text().split('from owned_progressive_source_samples_candidate import')[0]
exec(compile(setup,'scene_memory_capture','exec'));history.close()
from owned_closed_scene_memory import ClosedSceneMemory
profile=cProfile.Profile();times=[];expected=None
for iteration in range(16):
 begin=time.perf_counter_ns();profile.enable()
 try:owners=tuple(ClosedSceneMemory(scene.graph,rom) for scene in scenes)
 finally:profile.disable()
 times.append((time.perf_counter_ns()-begin)/1e6)
 values=tuple((m._ranges,m._starts,m.owned_byte_count) for m in owners)
 if expected is None:expected=values
 else:assert values==expected
 assert all(m.read(address,len(data))==data for m in owners for address,data in m._ranges)
functions=[]
for entry in profile.getstats():
 name=entry.code if isinstance(entry.code,str) else entry.code.co_name
 functions.append(dict(name=name,calls=entry.callcount,total_ms=entry.totaltime*1000,own_ms=entry.inlinetime*1000))
functions.sort(key=lambda x:x['own_ms'],reverse=True)
out=dict(result='PASS_CURRENT_SCENE_MEMORY_PROFILE',constructors=32,median_pair_profiled_ms=statistics.median(times),functions=functions,range_read_parity=True,scope='Current unmodified constructor captured pair with cProfile overhead; component equality/read verification, not live cadence or optimization comparison.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/current-scene-memory-profile.json').write_text(json.dumps(out,indent=2));print(out['result']);print(functions[:10])
