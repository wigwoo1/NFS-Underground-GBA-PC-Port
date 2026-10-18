"""Isolated readback backend; same current draw/present implementation."""
import ast,textwrap,ctypes as C
from pathlib import Path
import owned_source_d3d_sky_pan_display_candidate as display
path=Path(__file__).with_name('owned_source_d3d_sky_pan_display_candidate.py');text=path.read_text();tree=ast.parse(text);cls=next(x for x in tree.body if isinstance(x,ast.ClassDef));method=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='__init__');source=textwrap.dedent(ast.get_source_segment(text,method))
source=source.replace('owned-d3d-sky-pan-display-candidate.dll','owned-d3d-sky-stage-region-candidate.dll')
source=source.replace('assert d.nf_d3d_open()==0',"d.nf_d3d_material_packet_cached_profiled.argtypes=[P,C.c_size_t,P,C.c_uint,C.c_size_t,P,C.c_size_t]\n  d.nf_d3d_world_batch_profiled.argtypes=[P,C.c_uint,C.c_size_t,P,C.c_size_t,P,C.c_size_t,P,C.c_uint,C.c_size_t,P,C.c_size_t]\n  d.nf_d3d_source_hud_batch_profiled.argtypes=[P]*5+[C.c_size_t]\n  d.nf_d3d_read_region.argtypes=[C.c_uint]*4+[P,C.c_size_t]\n  assert d.nf_d3d_open()==0")
ns=dict(display.OwnedD3DConsumer.__init__.__globals__);exec(compile(source,'region-read-init','exec'),ns);display.OwnedD3DConsumer.__init__=ns['__init__']

