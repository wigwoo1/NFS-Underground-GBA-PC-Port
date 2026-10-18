"""Isolated strided material/link validation; every original guard remains."""
import inspect,textwrap
from functools import cached_property
from owned_graph_packet import GraphPacket
original=GraphPacket._parsed_graph
source=inspect.getsource(original.func).replace(' @cached_property\n','')
source=textwrap.dedent(source)
if source.startswith('@cached_property\n'):source=source[len('@cached_property\n'):]
needle="for j in range(n):\n   required.add(struct.unpack_from('<H',ring,j*68+44)[0]);links.add(struct.unpack_from('<H',ring,j*68+48)[0])"
assert source.count(needle)==1
source=source.replace(needle,"for material,link in struct.iter_unpack('<44xH2xH18x',ring):\n   required.add(material);links.add(link)")
namespace=dict(original.func.__globals__)
exec(compile(source,'bulk-strided-graph-validation','exec'),namespace)
parsed_graph=namespace['_parsed_graph']
def install():
 prop=cached_property(parsed_graph);prop.__set_name__(GraphPacket,'_parsed_graph');GraphPacket._parsed_graph=prop
def uninstall():GraphPacket._parsed_graph=original
