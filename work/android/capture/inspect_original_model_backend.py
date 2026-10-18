from pathlib import Path
import struct,json
folder=Path(r'C:\NFSUG-Workspace\NFSUG-android-arm-object-trace-local');rows=list(struct.iter_unpack('<20I',(folder/'original-object-path.bin').read_bytes()));active=None;calls=[];unpaired_returns=0
for row in rows:
 serial,frame,pc,op=row[:4];regs=row[4:]
 if pc==0x03002628:
  assert active is None;active=dict(source=regs[7],caller_frame=frame,context=regs[0],backend=[])
 elif pc in (0x030045e0,0x03004770):
  assert active is not None;active['backend'].append(dict(pc=hex(pc),frame=frame,r0=regs[0],r4=regs[4],r7=regs[7]))
  if pc==0x03004770:active['original_capture_gate']=regs[0]==1 and regs[4]==active['context']
 elif pc==0x0300262c:
  if active is None:unpaired_returns+=1;continue
  active['return_frame']=frame;active['caller_return_r0']=regs[0];calls.append(active);active=None
assert active is None and len(calls)==2 and all(any(e['pc']=='0x3004770' for e in c['backend']) for c in calls)
by_source={call['source']:call for call in calls}
assert by_source[33572092]['original_capture_gate'] is False and by_source[33571928]['original_capture_gate'] is True
assert all(call['backend'][0]['r0']==call['context'] and call['backend'][-1]['r4']==call['context'] for call in calls)
report=dict(result='PASS_ORIGINAL_MODEL_BACKEND_TRACE',trace_records=len(rows),unpaired_shared_tail_visits=unpaired_returns,calls=calls,capture_gate_source='live_scene.h: pc03004770 r0==1 and r4==live_scene.context');(folder/'model-backend-outcome-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
