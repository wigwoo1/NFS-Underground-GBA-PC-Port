import runpy,json,time
from pathlib import Path
import owned_wall_visibility_timed as timed
timed.install()
try:runpy.run_path('work/camera/run_dxgi_batch_candidate.py',run_name='__main__')
finally:
 path=Path('work/camera/prototype-runs')/('wall-native-traces-'+str(time.time_ns())+'.json')
 path.write_text(json.dumps(dict(records=timed.records,dropped=timed.dropped,scope='Optional native wall QPC/cycles and enclosing Python call, not pure GIL attribution'),indent=2));print(path)
