"""Bounded complete native-return outliers, no graphics/clock changes."""
import ctypes as C,json,time,threading
from pathlib import Path
import owned_material_caller_execution_install_candidate as execution
import owned_native_source_hud_cache_lease_session_candidate as hud
from owned_uncovered_window_candidate import OwnedD3DConsumer
latest={};outliers=[];totals={'bundle':0,'material':0};dropped=0
LIMIT=512
from owned_hud_prefetch_d3d_profile_install_candidate import PrefetchSession
prepare_original=PrefetchSession.prepare
def retain(kind,row):
 global dropped
 totals[kind]+=1
 if row['caller_end_ns']-row['native_end_ns']>1000000:
  if len(outliers)<LIMIT:outliers.append(dict(kind=kind,**row))
  else:dropped+=1
def bind(self):
 fn=self.source.nf_source_packet_bundle_profiled
 def bundle(*args):
  before=execution.sample();begin=time.perf_counter_ns();result=fn(*args);end=time.perf_counter_ns();after=execution.sample()
  assert result==0
  native=list(args[-2]);assert len(native)==4
  stats=list(args[12]);assert len(stats)==5
  row=dict(caller_begin_ns=begin,caller_end_ns=end,native_begin_ns=native[0],native_end_ns=native[1],native_cycles=native[3]-native[2],caller_execution=dict(thread=threading.get_ident(),before=list(before),after=list(after),raw_cycles=after[1]-before[1],cpu_ns=after[2]-before[2]),packet_stats=stats)
  latest[threading.get_ident()]=row;retain('bundle',row);return result
 self.source.nf_source_packet_bundle_profiled=bundle
def prepare(self,*args,**kwargs):
 if not getattr(self,"caller_return_selected",False):
  bind(self);self.caller_return_selected=True
 return prepare_original(self,*args,**kwargs)
PrefetchSession.prepare=prepare
namespace=OwnedD3DConsumer.render.__globals__
def observe(self,row):
 retain('material',dict(row))
 bundle=latest[threading.get_ident()];own=self.bundle_transfer_profile
 assert own['native_begin_ns']==bundle['native_begin_ns'] and own['native_end_ns']==bundle['native_end_ns']
 own['caller_execution']=bundle['caller_execution'];own['packet_stats']=bundle['packet_stats']
execution.observer=observe
def save():
 assert dropped==0 and totals['bundle']==totals['material'] and totals['bundle']>0,(totals,dropped)
 path=Path('work/camera/prototype-runs')/('caller-return-outliers-'+str(time.time_ns())+'.json')
 path.write_text(json.dumps(dict(totals=totals,capacity=LIMIT,dropped=dropped,threshold_ns=1000000,outliers=outliers,scope='Complete call counts; all >1ms native-return records retained if zero dropped. Getter overhead included, no causal GIL or physical60 claim.'),indent=2));print('CALLER_RETURN_LEDGER',path,flush=True)
