"""Opt-in bounded capture; captured run is not a timing benchmark."""
import runpy,sys,time,json,pickle
from pathlib import Path
import owned_native_source_process_preparation_candidate as source_process
from owned_scene_process_transport import pack
Base=source_process.ProcessPreparationService
class CapturingService(Base):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  self.route_folder=Path('work/camera/prototype-runs')/('source-route-'+str(time.time_ns()))
  self.route_folder.mkdir();self.route_rows=[];self.route_bytes=0
 def submit(self,older,newer,alphas=None,timeout=0,abort=None):
  if len(self.route_rows)<8:
   packets=(pack(*older),pack(*newer));payload=pickle.dumps(packets,protocol=5)
   if self.route_bytes+len(payload)<=256*1024*1024:
    name=str(len(self.route_rows))+'.pickle';(self.route_folder/name).write_bytes(payload)
    self.route_bytes+=len(payload)
    self.route_rows.append(dict(file=name,older=older[1].identity,newer=newer[1].identity,alphas=list(alphas),generation=self.pipeline.generation))
    (self.route_folder/'manifest.json').write_text(json.dumps(dict(rows=self.route_rows,bytes=self.route_bytes,scope='Local immutable scene diagnostics; capture overhead excludes timing comparison'),indent=2))
  return super().submit(older,newer,alphas,timeout,abort)
if __name__=='__main__':
 source_process.ProcessPreparationService=CapturingService
 runpy.run_path('work/camera/run_native_d3d_process_source_candidate.py',run_name='__main__')
