"""Isolated diagnostic retention change; no game or collector policy change."""
import pickle,json,time,gc
from pathlib import Path
class TraceRows:
 def __init__(self,capacity):self.capacity=capacity;self.encoded=[];self.bytes=0
 def append(self,row):
  if len(self.encoded)>=self.capacity:raise ValueError('Trace capacity exceeded')
  data=pickle.dumps(row,protocol=5)
  if len(data)>4096:raise ValueError('Trace row byte limit exceeded')
  self.encoded.append(data);self.bytes+=len(data)
 def __len__(self):return len(self.encoded)
 def __iter__(self):
  for data in self.encoded:yield pickle.loads(data)
 def snapshot(self):return list(self)
 def stats(self):return dict(records=len(self),capacity=self.capacity,bytes=self.bytes,tracked_storage_rows=sum(gc.is_tracked(x) for x in self.encoded),max_record_bytes=4096)
selected={}
def replace(module,capacity):
 assert type(module.rows) is list and not module.rows
 original=module.save;storage=TraceRows(capacity);module.rows=storage
 def save():
  module.rows=storage.snapshot()
  try:original()
  finally:module.rows=storage
 module.save=save;selected[module.__name__]=storage
 return storage
def install():
 import owned_parent_publication_tail_install_candidate as tail
 import owned_return_execution_live_candidate as stages
 import owned_parent_pair_retirement_install_candidate as retirement
 import owned_sample_readiness_margin_install_candidate as margins
 import owned_progressive_retirement_install_candidate as draw
 from live_owned_gpu_worker import LiveOwnedGPUWorker
 draw.owned_draw.__globals__['tail_rows']=replace(tail,8192)
 replace(stages,8192)
 LiveOwnedGPUWorker.draw_intervals.__globals__['retirement_rows']=replace(retirement,2048)
 replace(margins,8192)
def save():
 path=Path('work/camera/prototype-runs')/('serialized-execution-traces-'+str(time.time_ns())+'.json')
 path.write_text(json.dumps(dict(storage={k:v.stats() for k,v in selected.items()},scope='Only four experimental observer ledgers; bounded serialized private rows. Not all parent ownership or working set.'),indent=2));print('SERIALIZED_EXECUTION_TRACES',path,flush=True)
