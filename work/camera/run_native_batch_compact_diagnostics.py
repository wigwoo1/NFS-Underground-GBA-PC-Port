import runpy
from owned_world_preparation_service import WorldPreparationService
WorldPreparationService.compact_stage_diagnostics=True
runpy.run_path('work/camera/run_native_batch_ordered_draw_probe.py',run_name='__main__')
