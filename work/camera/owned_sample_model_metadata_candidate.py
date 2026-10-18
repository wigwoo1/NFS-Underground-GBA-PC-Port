"""Narrow sampled-model metadata: validate all extents, retain model blocks only."""
import inspect,textwrap
from owned_motion_pairs import _decode_records as reference
text=textwrap.dedent(inspect.getsource(reference))
needle='blocks.append(g[offset:offset+n]);offset+=n'
assert text.count(needle)==1
text=text.replace(needle,'if kind==3:blocks.append(g[offset:offset+n])\n   offset+=n')
text=text.replace('blocks=[]','blocks=[];block_bytes=0')
text=text.replace('if kind==3:blocks.append', 'block_bytes+=n\n   if kind==3:blocks.append')
text=text.replace('block_bytes=sum(map(len,blocks))','block_bytes=block_bytes')
namespace=dict(reference.__globals__)
exec(compile(text,'sampled-model-only-validated-metadata','exec'),namespace)
parse=namespace['_decode_records']
def decode(frame,trace=None):return parse(frame,source_keys='models',decode_trace=trace)

