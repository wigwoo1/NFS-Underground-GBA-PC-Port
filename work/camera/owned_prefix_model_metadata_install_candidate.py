"""Default-off lifecycle install for exact immutable prefix metadata reuse."""
from owned_prefix_model_metadata_candidate import records,clear,stats,local
installed=False
def install():
 global installed,old_anchor,old_mask,old_init,wrapper
 if installed:return
 import owned_source_model_anchor_candidate as anchors
 import owned_source_face_mask_candidate as masks
 from owned_progressive_source_samples_candidate import ProgressiveSourceWorldSamples as Samples
 old_anchor,old_mask,old_init=anchors.records,masks.records,Samples.__init__
 def init(self,*args,**kwargs):
  clear()
  try:return old_init(self,*args,**kwargs)
  finally:clear()
 wrapper=init;anchors.records=masks.records=records;Samples.__init__=wrapper;installed=True
def uninstall():
 global installed
 if not installed:return
 import owned_source_model_anchor_candidate as anchors
 import owned_source_face_mask_candidate as masks
 from owned_progressive_source_samples_candidate import ProgressiveSourceWorldSamples as Samples
 if anchors.records is not records or masks.records is not records or Samples.__init__ is not wrapper:raise RuntimeError('Prefix metadata installer ownership changed')
 anchors.records,masks.records,Samples.__init__=old_anchor,old_mask,old_init
 clear();installed=False
