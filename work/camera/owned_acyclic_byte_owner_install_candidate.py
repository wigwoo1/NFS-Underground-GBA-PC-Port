"""Avoid ctypes.cast self retention; immutable byte owners remain explicit."""
import ctypes as C,inspect,textwrap
from owned_source_segmented_draw_candidate import OwnedSourceDraw
from owned_hud_shared_library_binding_candidate import HudFrameSnapshot
for cls,old,new in [(OwnedSourceDraw,'C.cast(self.base_owner,C.c_void_p).value','C.c_void_p.from_buffer(self.base_owner).value'),(HudFrameSnapshot,'C.cast(retained,P).value','C.c_void_p.from_buffer(retained).value')]:
 method=cls.__init__;source=textwrap.dedent(inspect.getsource(method));assert source.count(old)==1
 source=source.replace(old,new);ns=dict(method.__globals__);exec(compile(source,'acyclic-byte-owner','exec'),ns);cls.__init__=ns['__init__']
