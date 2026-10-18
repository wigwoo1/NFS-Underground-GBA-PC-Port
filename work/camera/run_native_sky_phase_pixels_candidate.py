from pathlib import Path
path=Path('work/camera/run_native_exact_preparation_lifecycle_candidate.py');source=path.read_text();marker=' import owned_d3d_call_profile_install_candidate\n';assert source.count(marker)==1
source=source.replace(marker,marker+' import owned_sky_stage_render_tail_install_candidate\n import owned_sky_phase_backend_install_candidate\n import owned_sky_phase_pixels_install_candidate\n')
try:exec(compile(source,str(path),'exec'),dict(__name__='__main__',__file__=str(path)))
finally:
 import owned_exact_preparation_worker_install_candidate as preparation
 preparation.service.close()
 import owned_sky_phase_pixels_install_candidate as pixels
 pixels.save()
