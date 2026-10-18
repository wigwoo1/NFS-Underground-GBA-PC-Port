"""Default-off immutable wall candidate construction alternative."""
from collections import namedtuple
import owned_motion_wall_regions as regions
original=regions.WallRegionCandidate
Candidate=namedtuple('WallRegionCandidate','ordinal descriptor edge bounds region_flags wall')
def install():regions.WallRegionCandidate=Candidate
def restore():regions.WallRegionCandidate=original
