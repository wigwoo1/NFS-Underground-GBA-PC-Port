"""Count scene-memory read paths in actual captured source preparation."""
import runpy,json
from pathlib import Path
from bisect import bisect_right
from collections import Counter
from owned_closed_scene_memory import ClosedSceneMemory
original=ClosedSceneMemory.read;calls=Counter();sizes=Counter();failures=Counter()
def measured(self,address,size):
 end=address+size;index=max(0,bisect_right(self._starts,address)-1);offset=address-0x08000000
 rom=0<=offset and offset+size<=len(self.rom)
 contained=index<len(self._ranges) and self._ranges[index][0]<=address and end<=self._ranges[index][0]+len(self._ranges[index][1])
 probe=index
 if probe<len(self._ranges) and self._ranges[probe][0]+len(self._ranges[probe][1])<=address:probe+=1
 clear=probe>=len(self._ranges) or self._ranges[probe][0]>=end
 path='empty' if size==0 else ('contained_rom' if rom else 'contained_ram') if contained else 'direct_rom' if rom and clear else 'overlay_rom' if rom else 'assembled_ram'
 try:value=original(self,address,size)
 except ValueError:
  failures[path]+=1;raise
 calls[path]+=1;sizes[path]+=size;return value
ClosedSceneMemory.read=measured
try:runpy.run_path('work/camera/test_precomputed_source_eight_samples.py',run_name='__main__')
finally:ClosedSceneMemory.read=original
result=dict(result='MEASURED_WITH_PREPARED_PARITY_PASS',calls=dict(calls),requested_bytes=dict(sizes),failures=dict(failures),scope='Actual captured9111..9115 preparation/direct/precomputed parity workload; wrapper counts request paths, not timing or live race frequency.')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-memory-read-paths-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(result,indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(result))
