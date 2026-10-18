"""Isolated byte-block decoder selection in parent and actual preparation child."""
import types
import owned_child_road_wrapper_reuse_process_candidate as base
def install():
 import owned_motion_pairs as records
 from owned_record_small_blocks_candidate import decode_records
 records._decode_records=decode_records
 if hasattr(records._record_cache,'entries'):records._record_cache.entries.clear()
 assert records._decode_records is decode_records
install()
def request_child(*args):
 install()
 try:base.request_child(*args)
 finally:
  import json,os,time,gc
  from pathlib import Path
  import owned_motion_pairs as records
  entries=getattr(records._record_cache,'entries',[])
  blocks=[b for owner,header,rows in entries for k,c,bs,key in rows for b in bs]
  out=dict(pid=os.getpid(),entries=len(entries),blocks=len(blocks),tracked_blocks=sum(gc.is_tracked(b) for b in blocks),copied_bytes=sum(len(b) for b in blocks if type(b) is bytes),scope='Final current-thread record cache counters; final not peak retained state.')
  Path('work/camera/prototype-runs/small-block-child-'+str(time.time_ns())+'.json').write_text(json.dumps(out,indent=2))
class ProcessPreparationService(base.ProcessPreparationService):pass
original=base.ProcessPreparationService._initialize_request
ProcessPreparationService._initialize_request=types.FunctionType(original.__code__,dict(original.__globals__,request_child=request_child),original.__name__,original.__defaults__,original.__closure__)
