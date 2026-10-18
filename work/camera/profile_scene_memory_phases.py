import sys,json,time,statistics,inspect,types
from pathlib import Path
sys.argv=['fixture','work/camera/prototype-runs/child-scene-1791637661169682300']
setup=Path('work/camera/test_geometry_process_codec_component.py').read_text().split('from owned_progressive_source_samples_candidate import')[0]
exec(compile(setup,'phase_capture','exec'));history.close()
import owned_closed_scene_memory as memory
base=memory.ClosedSceneMemory.__init__;source=inspect.getsource(base)
source=source.replace('  self.rom=bytes(rom);','  begin=time.perf_counter_ns()\n  self.rom=bytes(rom);')
source=source.replace('  merged=[]','  collected=time.perf_counter_ns()\n  merged=[]')
source=source.replace('  self._ranges=tuple((a,bytes(d)) for a,d in merged);','  merged_at=time.perf_counter_ns()\n  self._ranges=tuple((a,bytes(d)) for a,d in merged);')
source+='  self.phase_ns=(collected-begin,merged_at-collected,time.perf_counter_ns()-merged_at)\n'
namespace=dict(memory.__dict__,time=time);import textwrap
exec(compile(textwrap.dedent(source),'scene_memory_phases','exec'),namespace)
# Source begins with one-space class-method indentation; normalize via dedent.
changed=namespace['__init__'];rows=[]
try:
 for i in range(16):
  memory.ClosedSceneMemory.__init__=base
  expected=tuple(memory.ClosedSceneMemory(scene.graph,rom) for scene in scenes)
  memory.ClosedSceneMemory.__init__=changed
  values=tuple(memory.ClosedSceneMemory(scene.graph,rom) for scene in scenes)
  for old,new in zip(expected,values):
   assert (old._ranges,old._starts,old.owned_byte_count)==(new._ranges,new._starts,new.owned_byte_count)
   rows.append(new.phase_ns)
finally:memory.ClosedSceneMemory.__init__=base
out=dict(result='PASS_SCENE_MEMORY_PHASE_PARITY',constructors=len(rows),median_ms={name:statistics.median(row[index] for row in rows)/1e6 for index,name in enumerate(('collection','sort_merge','freeze'))},scope='Captured pair scoped constructor timing with exact sparse ranges; instrumented component not live comparison.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/scene-memory-phases.json').write_text(json.dumps(out,indent=2));print(out)
