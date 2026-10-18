"""Avoid duplicate caller containers after a validated record cache miss."""
import inspect,textwrap
import owned_motion_pairs as module
source=textwrap.dedent(inspect.getsource(module.records))
line="  result=dict(refresh=header[0],epoch=header[1],ticks=header[2],records=[dict(kind=k,context=c,blocks=list(b),key=key) for k,c,b,key in rows])\n"
assert source.count(line)==1
source=source.replace(line,'')
namespace=dict(module.records.__globals__)
exec(compile(source,'record-cache-miss-container-reuse','exec'),namespace)
module.records.__code__=namespace['records'].__code__
