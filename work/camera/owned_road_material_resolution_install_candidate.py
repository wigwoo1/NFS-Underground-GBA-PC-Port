"""Opt-in child preparation material resolution; immutable scene local cache only."""
import owned_road_asset_cache as assets
from owned_road_material_resolution_candidate import road_candidates
stats=dict(calls=0,candidates=0)
def observed(closed,memory):
 result=road_candidates(closed,memory)
 stats['calls']+=1;stats['candidates']+=len(result)
 return result
def install():
 assets.road_candidates=observed
 print('ROAD_MATERIAL_RESOLUTION_SELECTED',flush=True)
