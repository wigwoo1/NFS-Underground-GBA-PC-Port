"""Reuse only the existing read branch that has proved no scene overlay."""
import inspect,textwrap
import owned_closed_scene_memory as memory
from owned_rom_slice_reuse_candidate import read_rom_slice
source=textwrap.dedent(inspect.getsource(memory.ClosedSceneMemory.read))
old='return self.rom[offset:offset+size]'
assert source.count(old)==1
source=source.replace(old,'return read_rom_slice(self.rom,offset,size)')
ns=dict(memory.ClosedSceneMemory.read.__globals__);ns['read_rom_slice']=read_rom_slice
exec(compile(source,'unoverlaid-rom-slice-reuse','exec'),ns)
memory.ClosedSceneMemory.read=ns['read']
