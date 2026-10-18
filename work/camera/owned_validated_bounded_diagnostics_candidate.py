"""Check every completed presentation before bounded retention can evict it."""
import struct
from owned_bounded_diagnostics_candidate import BoundedPresentationDiagnostics
from owned_present_interval_totals_candidate import PresentationIntervalTotals
class ValidatedPresentationDiagnostics(BoundedPresentationDiagnostics):
 def __init__(self,producer,context_count,**limits):
  super().__init__(**limits);self.producer=producer;self.context_count=context_count;self.validated_records=0;self.successful_presentations=0;self.cancelled_presentations=0;self.interval_totals=PresentationIntervalTotals()
 def _validate_tail(self):
  if self.tail is None:return
  row=self.tail
  if row['consumer_thread']==self.producer:raise ValueError('Presentation ran on producer thread')
  if row['context_count']!=self.context_count:raise ValueError('Unexpected renderer context count')
  result=row['native_result']
  if result not in (0,1,-1):raise ValueError('Unknown native presentation result')
  if result==1:
   commit=row['native_committed_sample']
   if commit is None:raise ValueError('Successful presentation missing native commit')
   if commit[:5]!=[row['epoch'],row['generation'],row['source_older'],row['refresh'],row['display_index']]:raise ValueError('Native commit source identity mismatch')
   if struct.unpack('<d',struct.pack('<Q',commit[5]))[0]!=row['alpha']:raise ValueError('Native commit alpha mismatch')
   if row.get('native_deadline_path'):
    stages=row['stages']
    if len(stages)!=7 or stages!=sorted(stages):raise ValueError('Invalid native stage order')
    timing=row['callback_timing']
    if timing['present_begin_ns']!=stages[3] or timing['present_end_ns']!=stages[4]:raise ValueError('Native presentation stage mismatch')
    if not stages[4]<=commit[6]<=row['transaction_end_ns'] or commit[6]<row['presentation_deadline_ns']:raise ValueError('Invalid native commit timestamp')
    if row['presentation']['status']!=0:raise ValueError('Successful presentation has failed native status')
  elif row['native_committed_sample'] is not None:raise ValueError('Unsuccessful presentation published commit')
  return result
 def append(self,row):
  result=self._validate_tail()
  previous=self.tail
  super().append(row)
  if previous is not None:self.interval_totals.observe(previous)
  if result is not None:
   self.validated_records+=1;self.successful_presentations+=result==1;self.cancelled_presentations+=result!=1
 def finalize(self,expected_frames=None):
  result=self._validate_tail()
  checked=self.validated_records+(result is not None)
  if checked!=self.total_records:raise ValueError('Whole-run diagnostic count mismatch')
  if expected_frames is not None and self.total_records!=expected_frames:raise ValueError('Expected presentation count mismatch')
  # Finalization must be repeatable without double-counting the mutable tail.
  import copy
  intervals=copy.copy(self.interval_totals)
  if self.tail is not None:intervals.observe(self.tail)
  return dict(self.stats(),whole_run_present_intervals=intervals.stats(),validated_records=checked,successful_presentations=self.successful_presentations+(result==1 if result is not None else 0),unsuccessful_presentations=self.cancelled_presentations+(result!=1 if result is not None else 0),whole_run_context_invariants_verified=True,full_run_telemetry_retained=self.dropped_records==0)
