import runpy,atexit,json,time
from pathlib import Path
import owned_object_chain_views_candidate as candidate
candidate.install()
def save():
 p=Path('work/camera/prototype-runs')/('object-chain-views-coverage-'+str(time.time_ns())+'.json');p.write_text(json.dumps(dict(calls=candidate.calls,scope='Includes cache hits; not distinct decoded owners.')));print(p)
atexit.register(save)
runpy.run_path('work/camera/run_combined_segmented_candidate.py',run_name='__main__')
