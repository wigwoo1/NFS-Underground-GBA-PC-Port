"""Isolated bounded projection type cache; arrays remain private."""
import ctypes as C,ast,textwrap
from pathlib import Path
from functools import lru_cache
import owned_preparation_fixed_types_install_candidate as fixed
import owned_source_native_depth_rectangle_candidate as face
@lru_cache(maxsize=128)
def _cached(length):return C.c_double*length
def projection_type(length):
 if type(length) is not int or length<0:raise ValueError('Invalid projection array length')
 # Larger extents retain original allocation behavior without entering the cache.
 return _cached(length) if length<=131072 else C.c_double*length
text=Path(face.__file__).read_text();tree=ast.parse(text);cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='SourceFaceDeterminants');fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='__init__');source=textwrap.dedent('\n'.join(text.splitlines()[fn.lineno-1:fn.end_lineno]))
assert source.count('C.c_double*(2*len(self.vertices))')==1
source=source.replace('C.c_double*(2*len(self.vertices))','projection_type(2*len(self.vertices))').replace('C.create_string_buffer(','private_string_buffer(')
namespace=dict(face.SourceFaceDeterminants.__init__.__globals__,private_string_buffer=fixed.private_string_buffer,projection_type=projection_type)
exec(compile(source,'bounded-projection-array-types','exec'),namespace)
def install():face.SourceFaceDeterminants.__init__=namespace['__init__']
