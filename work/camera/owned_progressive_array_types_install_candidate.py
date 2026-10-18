"""Bounded ctypes definition reuse; all published buffers remain private."""
import ctypes as C,inspect,textwrap,sys,ast
from pathlib import Path
from functools import lru_cache
from owned_progressive_pair_candidate import ProgressivePair
@lru_cache(maxsize=256)
def array_type(kind,length):
 if kind not in (C.c_double,C.c_uint32,C.c_uint8) or type(length) is not int or length<0:raise ValueError('Invalid sample array type')
 return kind*length
original=ProgressivePair.publish
# Generated method filenames cannot reliably identify source with inspect.
source_file=Path(__file__).with_name('owned_progressive_pair_candidate.py').read_text();tree=ast.parse(source_file);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ProgressivePair');node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='publish');source=ast.unparse(node)
if 'owned_sample_readiness_margin_install_candidate' in sys.modules:
 needle='        if not self.first.done():';assert source.count(needle)==1
 source=source.replace(needle,"        if not hasattr(self,'_margin_ready'):self._margin_ready={}\n        self._margin_ready[a]=time.perf_counter_ns()\n"+needle)
for old,new in [('(C.c_double * (len(raw) // 8))','array_type(C.c_double,len(raw)//8)'),('(C.c_uint32 * (n + 1))','array_type(C.c_uint32,n+1)'),('(C.c_uint8 * len(maskb))','array_type(C.c_uint8,len(maskb))')]:
 assert source.count(old)==1;source=source.replace(old,new)
namespace=dict(original.__globals__,array_type=array_type)
exec(compile(source,'bounded-progressive-array-types','exec'),namespace)
ProgressivePair.publish=namespace['publish']

assert ProgressivePair.publish.__code__.co_filename=="bounded-progressive-array-types"
assert ProgressivePair.publish.__globals__["array_type"] is array_type
