"""Isolated installation; buffer types reused, data arrays stay private."""
def install():
 import owned_source_presentation_batch_candidate as source
 import owned_prepared_world_motion as prepared
 from owned_source_model_anchor_types_candidate import SourceModelAnchors
 from owned_sampled_road_types_candidate import SampledRoadSequence
 source.SourceModelAnchors=SourceModelAnchors
 prepared.SampledRoadSequence=SampledRoadSequence
