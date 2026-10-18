"""Isolated split visibility phases plus native-boundary clock; no held-GIL mode."""
import atexit,json,runpy,time
from pathlib import Path
import owned_wall_visibility_phases as phases
import owned_wall_visibility_timed as native
phases.namespace['helper']=lambda:native.helper
phases.namespace['batch_types']=phases.original.batch_types
phases.namespace['table']=phases.original.table
phases.install()
def save():
 p=Path('work/camera/prototype-runs')/('visibility-native-phases-'+str(time.time_ns())+'.json');p.write_text(json.dumps(dict(records=phases.records,native_records=native.records,dropped=native.dropped,scope='Bounded diagnostic timestamps; no held-GIL mode. GC counters global/correlative. Native boundary and wrapper include scheduling effects; not physical display proof.'),indent=2));print(p)
atexit.register(save)
runpy.run_path('work/camera/run_combined_segmented_candidate.py',run_name='__main__')

