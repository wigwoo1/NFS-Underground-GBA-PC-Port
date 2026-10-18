"""Isolated traversal helper lifetime change; all arithmetic/order unchanged."""
import inspect,textwrap
import owned_portal_traversal as original
source=textwrap.dedent(inspect.getsource(original.traverse))
a=source.index('   def camera_point(point):')
b=source.index('   a=camera_point(point);b=camera_point(nextpoint)',a)
helper=source[a:b]
source=source[:a]+source[b:]
helper=''.join(line[2:] if line.startswith('  ') else line for line in helper.splitlines(True))
marker=' while index<len(queue):'
assert source.count(marker)==1
source=source.replace(marker,helper+marker)
namespace=dict(original.traverse.__globals__)
exec(compile(source,'portal-helper-hoist','exec'),namespace)
traverse=namespace['traverse']
