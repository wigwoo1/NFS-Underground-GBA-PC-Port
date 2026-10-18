"""Preserve existing imported function references in an isolated process."""
from owned_road_material_decode_reuse_candidate import original,candidate
original.__code__=candidate.__code__
