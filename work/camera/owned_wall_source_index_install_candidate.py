"""Opt-in wall source index binding; no automatic selection."""
import owned_motion_wall_regions as regions
from owned_graph_wall_sources_index_candidate import wall_sources as indexed
stats={'calls':0,'indexed_cache_hits':0}
def wall_sources(graph,**kwargs):
 cache=kwargs.get('material_cache')
 stats['calls']+=1
 if cache is not None and len(cache)>2:stats['indexed_cache_hits']+=1
 return indexed(graph,**kwargs)
regions.wall_sources=wall_sources
