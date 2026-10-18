"""Opt-in worker-local constructor selection; no global default promotion."""
from owned_road_record_construction_candidate import road_candidates
import owned_road_asset_cache as assets
import owned_endpoint_road_planner as planner
assets.road_candidates=road_candidates
planner.road_candidates=road_candidates
