"""Isolated immutable byte blocks reduce retained memoryview objects; copies payload."""
import inspect
import owned_motion_pairs as original
source=inspect.getsource(original._decode_records)
assert source.count("blocks.append(g[offset:offset+n])")==1
source=source.replace("blocks.append(g[offset:offset+n])","blocks.append(bytes(g[offset:offset+n]))")
namespace=dict(original.__dict__)
exec(compile(source,__file__,'exec'),namespace)
decode_records=namespace['_decode_records']
