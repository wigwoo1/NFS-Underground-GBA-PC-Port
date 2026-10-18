"""Isolated dedicated-worker static freeze lease; new objects keep normal GC."""
import gc,threading,time
class StaticFreezeLease:
 def __init__(self):self.owner=threading.get_ident();self.active=False;self.evidence={}
 def enter(self):
  if threading.get_ident()!=self.owner or self.active:raise RuntimeError('Static freeze owner/state mismatch')
  if gc.get_freeze_count():raise ValueError('Preexisting frozen objects cannot be leased')
  self.enabled=gc.isenabled();self.threshold=gc.get_threshold();begin=time.perf_counter_ns();collected=gc.collect();gc.freeze();self.active=True
  self.evidence=dict(frozen=gc.get_freeze_count(),startup_ns=time.perf_counter_ns()-begin,startup_collected=collected,automatic_gc_enabled=gc.isenabled(),thresholds=list(gc.get_threshold()),restored=False)
 def close(self):
  if threading.get_ident()!=self.owner:raise RuntimeError('Static freeze owner mismatch')
  if not self.active:return
  gc.unfreeze();self.active=False
  if gc.get_threshold()!=self.threshold or gc.isenabled()!=self.enabled:raise RuntimeError('Collection policy unexpectedly changed')
  self.evidence.update(restored=True,remaining_frozen=gc.get_freeze_count())
