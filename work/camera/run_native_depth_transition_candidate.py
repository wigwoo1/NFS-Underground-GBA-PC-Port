"""Isolated live depth-transition candidate; launcher remains unchanged."""
import runpy
import owned_source_presentation_batch_candidate as batch
from owned_source_depth_transition_candidate import SourceFaceDeterminants
batch.SourceFaceDeterminants=SourceFaceDeterminants
if __name__=='__main__':runpy.run_path('work/camera/run_native_d3d_backdrop_batch_candidate.py',run_name='__main__')
