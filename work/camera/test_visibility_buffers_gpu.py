import runpy,json
from pathlib import Path
import owned_visibility_buffers_candidate as candidate
candidate.install()
runpy.run_path('work/camera/test_combined_segmented_gpu.py',run_name='__main__')
assert candidate.calls_completed==10
Path('work/camera/visibility-buffers-coverage.json').write_text(json.dumps(dict(completed=candidate.calls_completed)))
print('PASS visibility buffer coverage',candidate.calls_completed)
