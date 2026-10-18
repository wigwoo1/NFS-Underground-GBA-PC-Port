"""Road material candidate in segmented full-scene original-GPU oracle."""
import runpy
from owned_road_material_resolution_candidate import install
install()
runpy.run_path('work/camera/test_combined_segmented_gpu.py',run_name='__main__')
