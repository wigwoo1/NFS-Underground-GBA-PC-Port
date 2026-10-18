import owned_source_native_depth_rectangle_candidate as original
from owned_source_batch_classify_candidate import SourceFaceDeterminants
original.SourceFaceDeterminants=SourceFaceDeterminants
import runpy
runpy.run_path('work/camera/run_segmented_wait_profile_candidate.py',run_name='__main__')
