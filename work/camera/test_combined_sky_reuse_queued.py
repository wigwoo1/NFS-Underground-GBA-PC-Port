"""Combined road material preparation and GPU sky-buffer full-scene oracle."""
import runpy
from owned_road_material_resolution_candidate import install as road_install
from owned_sky_attached_reuse_candidate import install as sky_install
road_install();sky_install()
runpy.run_path('work/camera/test_sky_buffer_fullscene_queued.py',run_name='__main__')
