"""Isolated narrow metadata only for source anchors/masks; cache cleared per pair."""
import threading,time
from owned_sample_model_metadata_candidate import decode
from owned_segmented_frame_candidate import SegmentedFrame
local=threading.local()
stats=dict(hits=0,misses=0)
installed=False
def clear():local.entries=[]
def records(frame,trace=None):
 start=time.perf_counter_ns() if trace is not None else None
 immutable=type(frame) is bytes or isinstance(frame,SegmentedFrame)
 entries=getattr(local,'entries',()) if immutable else ()
 for owner,result in entries:
  if owner is frame:
   stats['hits']+=1
   break
 else:
  stats['misses']+=1
  result=decode(frame)
  if immutable:local.entries=[*entries,(frame,result)][-2:]
 if trace is not None:
  end=time.perf_counter_ns();trace.append(dict(name='narrow_validated_model_metadata',started_ns=start,completed_ns=end,wall_ns=end-start))
 return dict(refresh=result['refresh'],epoch=result['epoch'],ticks=result['ticks'],records=[dict(kind=r['kind'],context=r['context'],key=r['key'],blocks=list(r['blocks'])) for r in result['records']])
def install():
 global installed,installed_init
 if installed:return
 import owned_source_model_anchor_candidate as anchors
 import owned_source_face_mask_candidate as masks
 from owned_progressive_source_samples_candidate import ProgressiveSourceWorldSamples
 global original_anchor_records,original_mask_records,original_init
 original_anchor_records=anchors.records;original_mask_records=masks.records;original_init=ProgressiveSourceWorldSamples.__init__
 anchors.records=records;masks.records=records
 def init(self,*args,**kwargs):
  clear()
  try:return original_init(self,*args,**kwargs)
  finally:clear()
 installed_init=init;ProgressiveSourceWorldSamples.__init__=init;installed=True

def uninstall():
 global installed
 if not installed:return
 import owned_source_model_anchor_candidate as anchors
 import owned_source_face_mask_candidate as masks
 from owned_progressive_source_samples_candidate import ProgressiveSourceWorldSamples
 if anchors.records is not records or masks.records is not records or ProgressiveSourceWorldSamples.__init__ is not installed_init:raise RuntimeError('Narrow metadata installer ownership changed')
 anchors.records=original_anchor_records;masks.records=original_mask_records;ProgressiveSourceWorldSamples.__init__=original_init
 clear();installed=False
