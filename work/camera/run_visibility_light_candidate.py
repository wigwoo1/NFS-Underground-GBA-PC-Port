import runpy,atexit,json,time
from pathlib import Path
import owned_visibility_light_trace as light
light.install()
def save():
 p=Path('work/camera/prototype-runs')/('visibility-light-'+str(time.time_ns())+'.json');p.write_text(json.dumps(dict(completed=light.completed,threshold_ns=light.threshold_ns,records=light.records,dropped=light.dropped,scope='Only native-domain completed calls >=1ms recorded; fixed per-thread scratch, no GC snapshots. Diagnostic overhead remains; no native internal timing or physical display proof.'),indent=2));print(p)
atexit.register(save)
runpy.run_path('work/camera/run_combined_segmented_candidate.py',run_name='__main__')
