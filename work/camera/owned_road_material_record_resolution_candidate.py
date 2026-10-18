"""Resolution memoization with existing verified record construction."""
import inspect
from owned_road_material_resolution_candidate import road_candidates as resolution
from owned_road_record_construction_candidate import record
namespace=dict(resolution.__globals__,RoadCandidate=record)
exec(compile(inspect.getsource(resolution),'material-record-resolution','exec'),namespace)
road_candidates=namespace['road_candidates']
