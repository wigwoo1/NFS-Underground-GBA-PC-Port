"""Partition presentation gaps using disjoint recorded consumer boundaries."""
import json,sys
from pathlib import Path

def analyze(report):
 samples=[x for x in report['presentation_samples'] if x.get('native_committed_sample')]
 results=[]
 for previous,current in zip(samples,samples[1:]):
  start=previous['native_committed_sample'][6];end=current['native_committed_sample'][6]
  if end-start<=33333333:continue
  if any(p['begin_ns']<end and p['end_ns']>start for p in report['pause_events']):continue
  points=[('before_consumer_dequeue',current['source_dequeued_ns']),('consumer_setup',current['pair_begin_ns']),('pair_acquisition',current['pair_ready_ns']),('sample_and_owner_packaging',current['batch_native_call_ns']),('native_before_draw',current['sample_begin_ns']),('native_draw',current['draw_complete_ns']),('native_wait_and_commit_setup',current['present_begin_ns']),('native_present',end)]
  cursor=start;parts=[]
  for name,boundary in points:
   clipped=max(cursor,min(end,boundary));parts.append(dict(stage=name,ms=(clipped-cursor)/1e6));cursor=clipped
  assert cursor==end and abs(sum(x['ms'] for x in parts)-(end-start)/1e6)<1e-8
  results.append(dict(display_index=current['display_index'],gap_ms=(end-start)/1e6,source_submit_after_previous_commit_ms=(current['source_submitted_ns']-start)/1e6,dequeue_after_submit_ms=(current['source_dequeued_ns']-current['source_submitted_ns'])/1e6,batch_sample_position=current['batch_sample_position'],parts=parts))
 return dict(result='PASS_DISJOINT_GAP_PARTITION',gaps=len(results),largest=sorted(results,key=lambda x:x['gap_ms'],reverse=True),scope='Disjoint clipped consumer timestamp intervals sum exactly to each gap. Before-dequeue includes producer availability and consumer scheduling; reused batch boundaries can predate gap. Pause-crossing gaps excluded explicitly here; authoritative cadence audit retains their nonpause residuals. No exclusive causality or scanout claim.')
if __name__=='__main__':
 rp,out=map(Path,sys.argv[1:3]);data=analyze(json.loads(rp.read_text()));out.write_text(json.dumps(data,indent=2));print(json.dumps(dict(gaps=data['gaps'],largest=data['largest'][:3]),indent=2))
