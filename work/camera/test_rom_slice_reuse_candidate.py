import json,sys,time,statistics
from pathlib import Path
report=json.loads(Path(sys.argv[1]).read_text());capture=Path(report['live_preparation_profiles'][0]['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('history=EndpointRoadPlanner')[0]
source=source.replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=capture')
exec(compile(source,'captured-road-input','exec'))
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
import owned_rom_slice_reuse_candidate as cache
original=ClosedSceneMemory.read
import owned_rom_slice_reuse_install_candidate
candidate=ClosedSceneMemory.read
memories=[ClosedSceneMemory(x.graph,rom) for x in scenes];baseline=[];timings=[[],[]]
try:
 for trial in range(24):
  for mode,read in enumerate((original,candidate)):
   ClosedSceneMemory.read=read;start=time.perf_counter_ns();values=[road_candidates(s.graph,m) for s,m in zip(scenes,memories)];timings[mode].append(time.perf_counter_ns()-start)
   if not baseline:baseline=values
   assert values==baseline
 # Reuse never intercepts scene overlays, even at a cached ROM address.
 m=ClosedSceneMemory.__new__(ClosedSceneMemory);m.rom=bytes(range(256))*64;m.missing=[];address=0x08000010;m._ranges=((address,b'changed!'),);m._starts=(address,)
 assert cache.read_rom_slice(m.rom,16,8)!=b'changed!'
 assert m.read(address,8)==b'changed!'
 assert m.read(address-2,12)==m.rom[14:16]+b'changed!'+m.rom[24:26]
 other=bytes([42])*16384;assert cache.read_rom_slice(other,16,8)==bytes([42])*8
 for i in range(80):cache.read_rom_slice(other,i*8,8)
 assert len(cache.local.entries)<=64 and cache.local.bytes<=2*1024*1024
 big=bytes(3*1024*1024)
 for i in range(3):assert cache.read_rom_slice(big,i*524288,1048576)==big[i*524288:i*524288+1048576]
 assert cache.local.bytes<=2*1024*1024
 oversized=cache.read_rom_slice(big,0,len(big));assert oversized==big and cache.local.bytes<=2*1024*1024
 for args in [(bytearray(10),0,1),(big,-1,1),(big,0,-1),(big,len(big),1)]:
  try:cache.read_rom_slice(*args)
  except (ValueError,TypeError):pass
  else:raise AssertionError('Invalid cache slice accepted')
 result=dict(result='PASS_CAPTURED_ROAD_ROM_SLICE_PARITY',comparisons=48,original_median_ms=statistics.median(timings[0])/1e6,candidate_median_ms=statistics.median(timings[1])/1e6,scope='Captured2scene road candidates plus overlay/ROM identity/capacity guards; component only, no live timing or native4K proof.')
 Path('work/camera/prototype-runs/rom-slice-reuse-evaluation-20261009.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
finally:ClosedSceneMemory.read=original;cache.clear()
