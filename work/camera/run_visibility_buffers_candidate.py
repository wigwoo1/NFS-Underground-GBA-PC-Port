import runpy,atexit,json,time
from pathlib import Path
import owned_visibility_buffers_candidate as candidate
candidate.install()
def save():
 p=Path('work/camera/prototype-runs')/('visibility-buffers-coverage-'+str(time.time_ns())+'.json');p.write_text(json.dumps(dict(completed=candidate.calls_completed,scope='Successful wrapper calls, includes fallback/empty cases; not native-only count.')));print(p)
atexit.register(save)
runpy.run_path('work/camera/run_combined_segmented_candidate.py',run_name='__main__')
