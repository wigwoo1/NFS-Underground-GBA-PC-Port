"""Isolated two-entry immutable record cache; decoded contents unchanged."""
import ast,types
from pathlib import Path
import owned_motion_pairs as module
source=Path(module.__file__).read_text();tree=ast.parse(source)
node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='records')
source=ast.get_source_segment(source,node)
assert source.count('entries[-4:]')==1
source=source.replace('entries[-4:]','entries[-2:]')
line="  result=dict(refresh=header[0],epoch=header[1],ticks=header[2],records=[dict(kind=k,context=c,blocks=list(b),key=key) for k,c,b,key in rows])\n"
assert source.count(line)==1;source=source.replace(line,'')
namespace=dict(module.records.__globals__);exec(compile(source,'two-entry-record-cache','exec'),namespace)
records=namespace['records']
