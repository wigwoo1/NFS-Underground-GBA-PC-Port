import runpy,json
from pathlib import Path
import owned_visibility_light_trace as light
light.install()
runpy.run_path('work/camera/test_combined_segmented_gpu.py',run_name='__main__')
assert light.completed==10
Path('work/camera/visibility-light-coverage.json').write_text(json.dumps(dict(completed=light.completed,slow=len(light.records),dropped=light.dropped)))
print('PASS lightweight coverage',light.completed)
