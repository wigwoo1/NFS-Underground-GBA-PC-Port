import owned_source_native_depth_rectangle_candidate as original
from owned_source_projection_scratch_candidate import SourceFaceDeterminants
original.SourceFaceDeterminants=SourceFaceDeterminants
import runpy
runpy.run_path('work/camera/test_segmented_original_gpu_parity.py',run_name='__main__')
