"""Install isolated performance candidates before renderer imports; defaults untouched."""
def install():
 import owned_closed_viewport as viewport
 from owned_closed_viewport_cache_candidate import ClosedViewport
 viewport.ClosedViewport=ClosedViewport
 from owned_closed_graph import ClosedGraph
 from owned_closed_camera_scan_candidate import ClosedGraph as Scanner
 ClosedGraph.match_frame=Scanner.match_frame
 import owned_sampled_road_sequence as roads
 from owned_road_dispatch_buffers_candidate import clipped_camera_road
 roads.clipped_camera_road=clipped_camera_road
 import owned_source_native_depth_rectangle_candidate as classification
 from owned_source_batch_classify_candidate import SourceFaceDeterminants
 classification.SourceFaceDeterminants=SourceFaceDeterminants
