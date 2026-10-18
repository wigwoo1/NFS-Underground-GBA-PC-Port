"""Release only calling preparation thread's decode cache after precomputation."""
from owned_precomputed_source_cached_library_candidate import PrecomputedSourceWorldSamples as Base
from owned_motion_pairs import _record_cache
from owned_model_key_records_candidate import _model_record_cache
class PrecomputedSourceWorldSamples(Base):
 def __init__(self,*args,**kwargs):
  try:super().__init__(*args,**kwargs)
  finally:_record_cache.entries=[];_model_record_cache.entries=[]
