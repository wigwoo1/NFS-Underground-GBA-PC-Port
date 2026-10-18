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
 base.request_child(*args)
class ProcessPreparationService(base.ProcessPreparationService):pass
original=base.ProcessPreparationService._initialize_request
ProcessPreparationService._initialize_request=types.FunctionType(original.__code__,dict(original.__globals__,request_child=request_child),original.__name__,original.__defaults__,original.__closure__)
