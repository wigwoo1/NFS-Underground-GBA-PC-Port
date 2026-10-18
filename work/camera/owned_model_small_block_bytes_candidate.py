"""Isolated small immutable block copy; mutable input retains original views."""
import inspect,textwrap
import owned_motion_pairs as source
import owned_model_key_records_candidate as model
stats=dict(calls=0)
original=source._decode_records
text=textwrap.dedent(inspect.getsource(original));assert text.count('blocks.append(g[offset:offset+n]);offset+=n')==1
text=text.replace('blocks.append(g[offset:offset+n]);offset+=n','blocks.append(bytes(g[offset:offset+n]) if n<=4096 else g[offset:offset+n]);offset+=n')
namespace=dict(original.__globals__);exec(compile(text,'model-small-private-blocks','exec'),namespace);candidate=namespace['_decode_records']
def decode(frame,source_keys=True,decode_trace=None):
 if type(frame) is bytes or isinstance(frame,source.SegmentedFrame):
  stats['calls']+=1
  return candidate(frame,source_keys,decode_trace)
 return original(frame,source_keys,decode_trace)
def install():model._decode_records=decode
