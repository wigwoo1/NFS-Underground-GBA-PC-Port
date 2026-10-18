"""Separate captured GL blit, SwapBuffers and restore wall time from scheduler wait."""
import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());g=json.loads(Path(sys.argv[2]).read_text());by={s['display_index']:s for s in r['presentation_samples'] if s.get('native_batch_candidate')};out=[]
for gap in g['largest']:
 s=by[gap['display_index']];p=s['native_present_stage_ns'];c=s['native_present_thread_cycles'];w=s['native_wait_timing'];t=s['native_commit_stage_ns']
 assert len(p)==3 and all(x>=0 for x in p) and len(w)==4 and w[1]==s['presentation_deadline_ns'] and w[0]<=w[2] and len(t)==7
 assert s['sample_begin_ns']<=s['draw_complete_ns']<=t[0]<=s['present_end_ns']
 assert sum(p)<=s['present_end_ns']-t[0]+100000
 out.append(dict(display_index=s['display_index'],gap_ms=gap['gap_ms'],draw_ms=(s['draw_complete_ns']-s['sample_begin_ns'])/1e6,blit_ms=p[0]/1e6,swap_ms=p[1]/1e6,restore_ms=p[2]/1e6,thread_cycles=c[:3],cycle_valid_mask=c[3],deadline_already_late_ms=max(0,w[0]-w[1])/1e6,token_wait_ms=(w[2]-w[0])/1e6,token_sleep_count=w[3]))
x=dict(result='PASS_PRESENT_WAIT_PARTITION',rows=out,scope='Captured native CPU wall durations. SwapBuffers includes driver/GPU/compositor/scheduling waits; no exclusive cause or physical scanout certification. Thread cycles are not elapsed time.')
Path(sys.argv[3]).write_text(json.dumps(x,indent=2));print(json.dumps(x,indent=2))

