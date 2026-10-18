"""Correlate consecutive observed display holds with exact submission callbacks."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());l=json.loads(Path(sys.argv[2]).read_text());p=json.loads(Path(sys.argv[3]).read_text());a=json.loads(Path(sys.argv[4]).read_text())
s=[x for x in r['presentation_samples'] if x.get('presentation_backend')=='dxgi_flip_sequential'];assert len(s)==len(l['rows'])==len(p['rows'])
sub={};shown={}
for row,t,phase in zip(s,l['rows'],p['rows']):
 assert t[4]==t[6] and t[5]==0 and t[0]==row['epoch'] and phase[16]==0
 assert row['native_commit_stage_ns'][3]<=phase[0]<=phase[7]<=row['native_commit_stage_ns'][4]
 sub[t[6]]=(row,t,phase)
 if t[7]==0 and t[8] and t[9]==t[10]:shown.setdefault(t[8],t[11]*1000000000//t[3])
rows=[]
for gap in a['multi_refresh_gaps']:
 if gap['pause_overlap'] is not False or gap['present_id_delta']!=1:continue
 details=[]
 for ident in [gap['before'],gap['after']]:
  row,t,phase=sub[ident];w=row['native_wait_timing'];assert shown[ident]>=row['native_commit_stage_ns'][3]
  parts={name:(phase[i+1]-phase[i])/1e6 for i,name in enumerate(p['phases'])}
  details.append(dict(present_id=ident,display_index=row['display_index'],draw_ms=(row['draw_complete_ns']-row['sample_begin_ns'])/1e6,token_wait_ms=(w[2]-w[0])/1e6,wake_lateness_ms=(w[2]-w[1])/1e6,dxgi_phases_ms=parts,display_after_callback_begin_ms=(shown[ident]-row['native_commit_stage_ns'][3])/1e6,display_after_callback_end_ms=(shown[ident]-row['native_commit_stage_ns'][4])/1e6))
 rows.append(dict(refresh_delta=gap['refresh_delta'],observed_display_gap_ms=(shown[gap['after']]-shown[gap['before']])/1e6,frames=details))
out=dict(result='PASS_EXACT_DISPLAY_HOLD_CORRELATION',holds=rows,scope='Consecutive flip present IDs observed two refreshes apart outside recorded pauses. Exact submission joins; display timestamp used only when SyncRefresh==PresentRefresh. Wall phases include scheduling/GPU/driver waits; no exclusive cause.')
Path(sys.argv[5]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
