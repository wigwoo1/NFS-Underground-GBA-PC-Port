"""Exact process job joins to native presentation gaps; overlap is not CPU causality."""
import json,sys
from pathlib import Path
from analyze_native_batch_active_gaps import analyze as gaps

def analyze(r):
 result=gaps(r);rows={x['display_index']:x for x in r['presentation_samples'] if 'display_index' in x};jobs={}
 for j in r['world_preparation_stage_samples']:jobs.setdefault((j['older'],j['newer']),[]).append(j)
 for g in result['largest']:
  row=rows[g['display_index']];present=row['native_present_stage_ns'];wait=row['native_wait_timing'];assert len(present)==3 and len(wait)==4 and wait[0]<=wait[2]
  g['present_stages_ms']=dict(blit=present[0]/1e6,swap_buffers=present[1]/1e6,after_swap=present[2]/1e6);g['native_deadline_wait_ms']=(wait[2]-wait[0])/1e6;g['native_deadline_sleep_count']=wait[3]
  matches=[j for j in jobs.get(tuple(g['source']),[]) if j.get('parent_completed_ns',float('inf'))<=row['pair_ready_ns']]
  if not matches:g['process_match']='missing authoritative parent completion';continue
  j=max(matches,key=lambda x:x['parent_completed_ns']);b=j['child_stages']['child_boundaries'];w=j['child_stages']['shared_write'];v=j['shared_read'];assert b['sent_ns']<=j['parent_received_ns']<=j['parent_completed_ns']<=row['pair_ready_ns']
  g['process_preparation']=dict(precompute_ms=(b['sampled_ns']-b['constructed_ns'])/1e6,construct_ms=(b['constructed_ns']-b['initialized_ns'])/1e6,encode_ms=(b['encoded_ns']-b['sampled_ns'])/1e6,shared_write_ms=(w['end_ns']-w['begin_ns'])/1e6,shared_read_ms=(v['end_ns']-v['begin_ns'])/1e6,parent_decode_ms=j['parent_output_decode_ns']/1e6,ready_before_acquire_ms=(row['pair_ready_ns']-j['parent_completed_ns'])/1e6,largest_sample_stages=sorted([dict(alpha=s['alpha'],name=a['name'],wall_ms=a['wall_ns']/1e6) for s in j['child_stages'].get('sample_timings',[]) for a in s.get('assembly_stages',[])],key=lambda x:x['wall_ms'],reverse=True)[:6])
 result['scope']+=' Process pairs use latest authoritative parent completion before acquisition; nested stages cannot be added as exclusive CPU costs.'
 return result
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out['largest'][:3],indent=2))
