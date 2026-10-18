import atexit,json,runpy,time
from pathlib import Path
import owned_wall_visibility_phases as phases
phases.install()
def save():
 p=Path('work/camera/prototype-runs')/('visibility-phases-'+str(time.time_ns())+'.json');p.write_text(json.dumps(dict(records=phases.records,scope='Bounded native-domain visibility phase diagnostics; global GC counters are correlation only, overhead perturbs timing, fallback calls not recorded.'),indent=2));print(p)
atexit.register(save)
runpy.run_path('work/camera/run_combined_segmented_candidate.py',run_name='__main__')
