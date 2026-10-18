"""Isolated selected-target CPU readback diagnostics; never timing certification."""
import sys,runpy,json,time
from pathlib import Path
import live_source_sky_pixels_candidate as diagnostic
sys.modules['live_source_batch_candidate']=diagnostic

# Anchor runner assigns cleanup itself; export at process exit from tracked instance.
import atexit
instances=[]
init=diagnostic.SourceBatchWorker.__init__
def tracked(self,*args,**kwargs):
 init(self,*args,**kwargs);instances.append(self)
diagnostic.SourceBatchWorker.__init__=tracked
def export():
 path=Path('work/camera/prototype-runs')/('selected-sky-pixels-'+str(time.time_ns())+'.json')
 path.write_text(json.dumps(dict(scope='Selected queue target before presentation, diagnostic synchronous readback affects cadence. Crop may contain foreground; not physical scanout.',records=[row for obj in instances for row in getattr(obj,'sky_pixel_diagnostics',[])]),indent=2));print(path)
atexit.register(export)
original_run_path=runpy.run_path
def redirect(path,*args,**kwargs):
 if path=='work/camera/run_owned_native_prototype.py':path='work/camera/run_owned_gentle_sky_diagnostic.py'
 return original_run_path(path,*args,**kwargs)
runpy.run_path=redirect
runpy.run_path('work/camera/run_source_compact_diagnostics_candidate.py',run_name='__main__')

