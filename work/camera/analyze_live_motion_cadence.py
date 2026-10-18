"""Observed completed presentation cadence; does not certify monitor scanout."""
import json,sys,statistics
from pathlib import Path
path=Path(sys.argv[1]);r=json.loads(path.read_text())
rows=[x for x in r['presentation_samples'] if x.get('interpolated') and x.get('hidden_window_presented')]
assert len(rows)>1
period=1e9/60
indices=[x['display_index'] for x in rows]
gaps=[b['present_end_ns']-a['present_end_ns'] for a,b in zip(rows,rows[1:])]
late=[x['present_end_ns']-x['presentation_deadline_ns'] for x in rows]
def stats(a):
 a=sorted(a);return dict(count=len(a),median_ms=statistics.median(a)/1e6,p95_ms=a[int(.95*(len(a)-1))]/1e6,max_ms=max(a)/1e6)
stalls=[dict(older=a['refresh'],newer=b['refresh'],display_index=b['display_index'],gap_ms=g/1e6,pair_prepare_ms=b.get('pair_prepare_ns',0)/1e6,native_draw_ms=(b.get('native_draw_elapsed_ns') or 0)/1e6) for a,b,g in zip(rows,rows[1:],gaps) if g>2*period]
if all('slot_begin_ns' in x for x in rows):
 for stall in stalls:
  i=indices.index(stall['display_index']);a,b=rows[i-1],rows[i]
  parts=dict(before_slot=b['slot_begin_ns']-a['present_end_ns'],input_poll=b['input_poll_ns'],sample=b['pose_sample_cpu_ns'],draw=b['draw_cpu_ns'],post_draw=b['draw_complete_ns']-(b['sample_begin_ns']+b['pose_sample_cpu_ns']+b['draw_cpu_ns']),pacing=b['pacing_wait_ns'],present=b['present_end_ns']-b['present_begin_ns'])
  assert abs(sum(parts.values())-(b['present_end_ns']-a['present_end_ns']))<=1
  stall['gap_stages_ms']={k:v/1e6 for k,v in parts.items()}
  if b['pair_begin_ns']!=a['pair_begin_ns']:
   stall['boundary_stages_ms']=dict(until_dequeue=(b['source_dequeued_ns']-a['present_end_ns'])/1e6,dequeue_to_pair=(b['pair_begin_ns']-b['source_dequeued_ns'])/1e6,pair_prepare=(b['pair_ready_ns']-b['pair_begin_ns'])/1e6,pair_ready_to_slot=(b['slot_begin_ns']-b['pair_ready_ns'])/1e6)
  stall['native_stages_ms']={k:b[k]/1e6 for k in ('native_input_poll_ns','native_draw_elapsed_ns','native_present_ns') if b.get(k) is not None}
out=dict(scope='CPU completed presentations; timing jitter and stalls observed, no scanout certification',clock_ratio=r['timing']['simulated_seconds']/r['timing']['wall_seconds'],contiguous=all(b==a+1 for a,b in zip(indices,indices[1:])),gaps=stats(gaps),deadline_lateness=stats(late),gaps_over_two_refreshes=len(stalls),catchup_gaps_under_half_refresh=sum(g<period/2 for g in gaps),frames_over_one_refresh_late=sum(x>period for x in late),largest_stalls=sorted(stalls,key=lambda x:x['gap_ms'],reverse=True)[:20])
output=path.with_suffix('.motion-cadence.json');output.write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
