"""Avoid duplicate model metadata caller containers on a validated cache miss."""
import inspect,textwrap
import owned_model_key_records_candidate as module
original=module.records
source=textwrap.dedent(inspect.getsource(original))
line="  result=dict(refresh=header[0],epoch=header[1],ticks=header[2],records=[dict(kind=k,context=c,blocks=list(b),key=key) for k,c,b,key in rows])\n"
assert source.count(line)==1
source=source.replace(line,'')
namespace=dict(original.__globals__)
exec(compile(source,'model-record-miss-container-reuse','exec'),namespace)
module.records.__code__=namespace['records'].__code__
