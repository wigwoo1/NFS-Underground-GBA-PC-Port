import owned_complete_road_gpu as road
from owned_road_encode_flat_join_candidate import encode_road
# Preserve all previously imported aliases to the authoritative encoder function.
road.encode_road.__code__=encode_road.__code__
