"""Per-traversal camera transform reuse, keyed by exact source x/z bytes."""
import inspect,textwrap
import owned_portal_traversal as original
source=textwrap.dedent(inspect.getsource(original.traverse))
source=source.replace(' queue=[tuple(root[:7])];index=0;linked=False',' point_cache={}\n queue=[tuple(root[:7])];index=0;linked=False')
needle='   def camera_point(point):\n    x,z='
assert source.count(needle)==1
source=source.replace(needle,"   def camera_point(point):\n    key=point[:8];cached=point_cache.get(key)\n    if cached is not None:return cached\n    x,z=")
source=source.replace('if sampled_camera is None:return transform(x,z,matrix)','if sampled_camera is None:\n     result=transform(x,z,matrix);point_cache[key]=result;return result')
source=source.replace('if endpoint_correction is None:return result','if endpoint_correction is None:point_cache[key]=result;return result')
source=source.replace('    return tuple(result[k]+(1-alpha)*delta_a[k]+alpha*delta_b[k] for k in range(2))','    result=tuple(result[k]+(1-alpha)*delta_a[k]+alpha*delta_b[k] for k in range(2));point_cache[key]=result;return result')
namespace=dict(original.traverse.__globals__)
exec(compile(source,'portal-point-local-cache','exec'),namespace)
traverse=namespace['traverse']
