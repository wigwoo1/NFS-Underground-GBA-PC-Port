"""Isolated per-selection edge reuse; cache never crosses alpha or portal owners."""
from pathlib import Path
import owned_sampled_graph_wall_visibility as original
source=Path(original.__file__).read_text()
source=source.replace('selected=[];pending=[];calls=[]','selected=[];pending=[];calls=[];edge_cache={}')
needle='edge=sampled_edge(candidate.wall,ring,old_camera,new_camera,camera,portal.endpoints,alpha,offsets)'
assert source.count(needle)==1
source=source.replace(needle,"key=(candidate.descriptor,candidate.edge)\n  if key not in edge_cache:edge_cache[key]=sampled_edge(candidate.wall,ring,old_camera,new_camera,camera,portal.endpoints,alpha,offsets)\n  edge=edge_cache[key]")
namespace=dict(__name__=__name__);exec(compile(source,str(Path(__file__)),'exec'),namespace)
selected_graph_walls=namespace['selected_graph_walls']
def install():
 import owned_sampled_graph_gpu as gpu
 gpu.selected_graph_walls=selected_graph_walls
