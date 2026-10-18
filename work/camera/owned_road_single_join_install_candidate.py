"""Opt-in encoder replacement preserving all imported authoritative aliases."""
import owned_complete_road_gpu as road
from owned_road_single_join_candidate import encode_road
road.encode_road.__code__=encode_road.__code__
