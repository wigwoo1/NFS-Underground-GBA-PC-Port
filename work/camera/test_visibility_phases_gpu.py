import runpy,json
from pathlib import Path
import owned_wall_visibility_phases as phases
phases.install()
runpy.run_path('work/camera/test_combined_segmented_gpu.py',run_name='__main__')
assert phases.records
Path('work/camera/visibility-phase-gpu.json').write_text(json.dumps(dict(records=phases.records,scope='Instrumented native-domain calls only; fallback behavior unchanged and not recorded.'),indent=2))
print('PASS visibility phase records',len(phases.records))
