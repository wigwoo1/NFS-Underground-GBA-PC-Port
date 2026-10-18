"""Explicit candidate selection only; cached endpoint object visits owned by pair."""
import owned_sampled_world_segmented_candidate as world
from owned_sampled_model_visit_index_candidate import sampled_model_visit as indexed
stats={'calls':0,'index_present_before_call':0}
def sampled_model_visit(pair,alpha,object_index=None):
 stats['calls']+=1
 stats['index_present_before_call']+=int(hasattr(pair,'_ordinary_visit_object_index'))
 return indexed(pair,alpha,object_index)
world.sampled_model_visit=sampled_model_visit

import owned_sampled_world_frame as baseline_world
baseline_world.sampled_model_visit=sampled_model_visit

from owned_prepared_world_motion import PreparedWorldMotion
_original_close=PreparedWorldMotion.close
def close(self):
 try:return _original_close(self)
 finally:
  pair=getattr(self,'pair',None)
  if pair is not None and hasattr(pair,'_ordinary_visit_object_index'):
   del pair._ordinary_visit_object_index
PreparedWorldMotion.close=close
