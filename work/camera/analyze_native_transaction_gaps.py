"""Partition actual committed gaps without summing concurrent producer work."""
import json,sys
from pathlib import Path
from analyze_live_gap_phases import overlap

def analyze(r):
 rows=[x for x in r['presentation_samples'] if x.get('native_transaction_candidate')]
 assert rows
 gaps=[];excluded=[]
 for old,new in zip(rows,rows[1:]):
  left=old['native_committed_sample'][6];right=new['native_committed_sample'][6]
  assert right>=left
  pause=sum(max(0,min(right,p['end_ns'])-max(left,p['begin_ns'])) for p in r['pause_events'])
  if pause:excluded.append(new['display_index']);continue
  if right-left<=1e9/30:continue
  same=(old['epoch'],old['source_older'],old['refresh'])==(new['epoch'],new['source_older'],new['refresh'])
  b=new['native_draw_boundary'];assert left<=right and new['transaction_begin_ns']<=b[0]<=b[1]<=right
  phases=dict(prior_commit_to_sample=overlap(left,new['sample_begin_ns'],left,right),sample_and_context=overlap(new['sample_begin_ns'],new['transaction_begin_ns'],left,right),native_entry=overlap(new['transaction_begin_ns'],b[0],left,right),native_draw=overlap(b[0],b[1],left,right),wait_and_commit=overlap(b[1],right,left,right))
  assert abs(sum(phases.values())-(right-left)/1e6)<.001
  w=new['native_wait_timing'];st=new['native_commit_stage_ns']
  native_detail=dict(wait_ms=(w[2]-w[0])/1e6,deadline_from_wait_ms=(w[1]-w[0])/1e6,sleeps=w[3],presentation_lock_ms=(st[1]-st[0])/1e6,queue_lock_ms=(st[2]-st[1])/1e6,present_callback_ms=(st[4]-st[3])/1e6,native_swap_ms=new['native_present_stage_ns'][1]/1e6)
  gaps.append(dict(native_detail=native_detail,index=new['display_index'],same_pair=same,gap_ms=(right-left)/1e6,phases_ms=phases,native_draw_cycles=b[2],dominant=max(phases,key=phases.get),pair_ready_before_previous_commit=new['pair_ready_ns']<=left,previous_return_delay_ms=max(0,old['transaction_return_ns']-left)/1e6))
 return dict(scope='Disjoint serial host-clock intervals covering native commit gaps; intentional pause crossings excluded. Prior commit-to-sample includes prior Python return, queue, preparation, and scheduling; not exclusive cause proof.',long_gaps=len(gaps),same_pair_long_gaps=sum(x['same_pair'] for x in gaps),cross_pair_long_gaps=sum(not x['same_pair'] for x in gaps),dominant_counts={k:sum(x['dominant']==k for x in gaps) for k in ('prior_commit_to_sample','sample_and_context','native_entry','native_draw','wait_and_commit')},excluded_pause_crossings=excluded,largest=sorted(gaps,key=lambda x:x['gap_ms'],reverse=True)[:20])
if __name__=='__main__':
 r=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
