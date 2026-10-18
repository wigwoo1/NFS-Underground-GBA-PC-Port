"""Explicit diagnostic selection of bounded per-traversal point reuse."""
import owned_portal_traversal as original
from owned_portal_traversal_point_local_candidate import traverse as candidate
stats={'calls':0}
def traverse(*args,**kwargs):
 stats['calls']+=1
 return candidate(*args,**kwargs)
import owned_motion_visibility as visibility
import owned_wall_region_candidates as regions
original.traverse=traverse
visibility.traverse=traverse
regions.traverse=traverse
