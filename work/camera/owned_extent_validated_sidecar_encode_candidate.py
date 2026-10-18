import types
from owned_source_process_sidecar_candidate import encode as original
from owned_source_extent_sidecar_candidate import decode
namespace=dict(original.__globals__,decode=decode)
encode=types.FunctionType(original.__code__,namespace,original.__name__,original.__defaults__,original.__closure__)
