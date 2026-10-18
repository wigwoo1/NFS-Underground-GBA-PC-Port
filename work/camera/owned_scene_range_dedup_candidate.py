"""Elide exact duplicate sparse ranges before original overlap validation."""
import inspect
import owned_closed_scene_memory as original
source=inspect.getsource(original.ClosedSceneMemory)
needle='self.rom=bytes(rom);self._ranges=[];self.missing=[];'
assert source.count(needle)==1
source=source.replace(needle,needle+'seen_ranges={};self.range_dedup_hits=0;')
needle='if data:self._ranges.append((address,data))'
assert source.count(needle)==1
source=source.replace(needle,"if data:\n    key=(address,len(data));prior=seen_ranges.get(key)\n    if prior is not None and prior==data:self.range_dedup_hits+=1;return\n    seen_ranges[key]=data;self._ranges.append((address,data))")
namespace=dict(original.__dict__)
exec(compile(source,'exact-scene-range-dedup','exec'),namespace)
ClosedSceneMemory=namespace['ClosedSceneMemory']
def install():original.ClosedSceneMemory=ClosedSceneMemory
