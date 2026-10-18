import runpy,json
from pathlib import Path
runpy.run_path('work/camera/run_native_callback_cycles_candidate.py',run_name='__main__')
import owned_native_callback_cycles_install_candidate as profile
assert len(profile.rows)>100 and profile.dropped==0
Path('work/camera/prototype-runs/native-callback-cycles-20261009.json').write_text(json.dumps(dict(rows=profile.rows,dropped=profile.dropped),indent=2));print('PASS_ACTUAL_NATIVE_CALLBACK_CYCLES_CAPTURE',len(profile.rows))
