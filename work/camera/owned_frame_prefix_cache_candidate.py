"""Opt-in pair-owned immutable prefix reuse; sampled bounds/cameras remain fresh."""
import inspect
from collections import OrderedDict
from owned_segmented_frame_candidate import SegmentedFrame
stats=dict(hits=0,misses=0,evictions=0,joined_bytes=0,reused_bytes=0)
def join_frame_cached(pair,header,geometry,base,tail_offset):
 geometry=tuple(geometry)
 if type(header) is not bytes or len(header)!=40 or len(geometry)>4094 or any(type(x) is not bytes for x in geometry):raise ValueError('Invalid immutable prefix inputs')
 if not hasattr(pair,'_immutable_prefix_cache'):pair._immutable_prefix_cache=OrderedDict();pair._immutable_prefix_bytes=0
 cache=pair._immutable_prefix_cache;key=(header,geometry)
 if key in cache:
  prefix=cache[key];cache.move_to_end(key);stats['hits']+=1;stats['reused_bytes']+=len(prefix)
 else:
  prefix=b''.join((header,*geometry));stats['misses']+=1;stats['joined_bytes']+=len(prefix)
  # Validate before publishing any cached bytes.
  frame=SegmentedFrame(prefix,base,tail_offset)
  if 2*len(prefix)<=32*1024*1024:
   while cache and (len(cache)>=8 or pair._immutable_prefix_bytes+2*len(prefix)>32*1024*1024):
    _,old=cache.popitem(last=False);pair._immutable_prefix_bytes-=2*len(old);stats['evictions']+=1
   cache[key]=prefix;pair._immutable_prefix_bytes+=2*len(prefix)
  return frame
 return SegmentedFrame(prefix,base,tail_offset)
def install():
 import owned_prepared_world_segmented_candidate as prepared
 original=prepared.PreparedWorldMotion.sample.__globals__['assemble_world']
 source=inspect.getsource(original);marker='frame=join_frame(struct.pack'
 assert source.count(marker)==1
 source=source.replace(marker,'frame=join_frame_cached(pair,struct.pack')
 namespace=dict(original.__globals__,join_frame_cached=join_frame_cached)
 exec(compile(source,'immutable-pair-prefix-cache','exec'),namespace)
 prepared.PreparedWorldMotion.sample.__globals__['assemble_world']=namespace['assemble_world']
