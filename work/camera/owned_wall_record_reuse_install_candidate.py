from owned_sampled_graph_record_reuse_candidate import sampled_graph_gpu_records
import owned_sampled_world_segmented_candidate as world
world.sampled_graph_gpu_records=sampled_graph_gpu_records
import owned_prepared_world_segmented_candidate as prepared
original_close=prepared.PreparedWorldMotion.close

def clear_closed_wall_records(self):
 pair=getattr(self,'pair',None);portal=getattr(pair,'portal',None)
 cache=getattr(portal,'_complete_wall_record_cache',None)
 if cache is not None:cache.records.clear();cache.bytes=0

def release_closed_wall_records(self):
 clear_closed_wall_records(self)
 return original_close(self)
prepared.PreparedWorldMotion.close=release_closed_wall_records
