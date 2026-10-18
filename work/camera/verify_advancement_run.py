"""Candidate-only audit; strict default verifiers remain unchanged."""
import json,math,struct,sys
from pathlib import Path
from owned_motion_clock import deadline

def verify(r):
 assert r['result']=='SMOKE_COMPLETE'
 rows=[x for x in r['presentation_samples'] if x.get('native_committed_sample')];assert rows
 sources={(s['epoch'],s['publication']):s for s in r['sky_capture_records']};skipped=0
 for i,x in enumerate(rows):
  assert x['display_advancement_candidate'] and x['full_scene_sampled'] and x['complete_scene_pair_retained'] and x['sky_interpolated']
  c=x['native_committed_sample'];a=x['display_advance_audit'];assert len(a)==4
  assert c[:5]==[x['epoch'],x['generation'],x['source_older'],x['refresh'],x['display_index']]
  assert struct.unpack('<d',struct.pack('<Q',c[5]))[0]==x['alpha']
  assert x['present_begin_ns']<=c[6]<=x['commit_return_ns'] and c[6]>=x['presentation_deadline_ns']
  old=sources[x['epoch'],x['source_older']];new=sources[x['epoch'],x['refresh']];assert old['asset_origin']==new['asset_origin']
  delta=((new['angle']-old['angle']+8192)&16383)-8192;assert abs(delta*240/4096)<120
  angle=(new['angle']&16383) if x['alpha']==1 else (old['angle']&16383)+delta*x['alpha'];phase=(angle*240/4096)%240
  assert x['sky_fraction']==phase-math.floor(phase)
  if i:
   p=rows[i-1];gap=x['display_index']-p['display_index'];assert gap>=1 and a[:2]==[p['display_index'],gap-1]
   assert c[7]==p['native_committed_sample'][7]+1
   if a[1]:
    expected=x['presentation_deadline_ns']-(deadline(0,x['display_index'])-deadline(0,x['display_index']-1))
    assert a[2]==expected and a[2]<=a[3]<=x['native_draw_boundary'][0]
    plan=x['display_advance_plan'];assert plan['previous_index']==a[0] and plan['target_index']==x['display_index'] and plan['skipped_count']==a[1]
   else:assert a[2:]==[0,0]
   skipped+=a[1]
 for p in r['pause_events']:
  ack=p['native_pause_ack_ns'];resume=p['native_resume_ack_ns'];assert ack<=resume
  assert not any(ack<=x['native_committed_sample'][6]<resume for x in rows)
  planned=p['buffer_at_begin']['planned_replay_indices'];after=[x['display_index'] for x in rows if x['native_committed_sample'][6]>=resume]
  assert all(after.count(index)==1 for index in planned),'Pending pause replay missing or duplicated'
 s=r['shutdown_evidence'];assert s['active_contexts_after_close']==0 and not s['gpu_thread_alive'] and not s['preparation_thread_alive'] and s['native_owner_released']
 return dict(result='PASS_CANDIDATE_COMMIT_SKY_PAUSE_INVARIANTS',committed=len(rows),skipped_display_slots=skipped,pause_events=len(r['pause_events']),scope='Native skipped-slot grid/audit, exact sky phase, no commits while pause acknowledged, each planned pending display replayed once, clean shutdown. No60fps, physicalscanout/controller or independent visual fidelity claim.')
if __name__=='__main__':
 r=json.loads(Path(sys.argv[1]).read_text());out=verify(r);Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
