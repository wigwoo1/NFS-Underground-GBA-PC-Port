"""Verify bounded producer evidence; does not repair or reinterpret rotations."""
from pathlib import Path
import hashlib,json
base=Path(r'C:\NFSUG-Workspace')
root=Path(__file__).resolve().parent
out=base/'NFSUG-pc-rotation-trace-core'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((out/'rotation-trace-build-report.json').read_text())
t=json.loads((out/'rotation-trace-core-test-report.json').read_text())
p=json.loads((out/'probe/background-gap-probe-report.json').read_text())
old=json.loads((base/'NFSUG-pc-first-model-failure-core/probe/background-gap-probe-report.json').read_text())
d=json.loads((out/'probe/rotation-events.json').read_text())
assert b['core_sha256']==t['core_sha256']==p['core_sha256']==sha(out/'capture-host.dll')
assert t['result']=='PASS_ROTATION_TRACE_CORE_PARITY'
for name,h in b['maintained_source_sha256'].items():assert sha(root/name)==h,name
assert p['script_sha256']==sha(root/'probe_rotation_producers.py')
assert t['maintained_test_sha256']==sha(root/'test_rotation_trace_core.py')
assert all(t[k] for k in ['all_original_pixels_exact','all_complete_source_bytes_exact','no_capture_logic_steps','transfers_balanced','diagnostic_short_buffer_atomic'])
assert p['audio_sha256']==old['audio_sha256'] and p['audio_frames']==old['audio_frames']
assert [x['logic_step'] for x in p['failures']]==[x['logic_step'] for x in old['failures']]==list(range(3519,3551))
h=d['header'];rs=d['records'];assert h[3]==len(rs)==45 and h[6]==848 and h[8]==0
assert len((out/'probe/rotation-trace.bin').read_bytes())==h[2]*4
for serial in range(840,848):
 producers=[r for r in rs if r[2]==serial and r[3]==1]
 consumers=[r for r in rs if r[2]==serial and r[3]==4]
 assert len(producers)==len(consumers)==1
 assert producers[0][6]==consumers[0][29]==0x0200c24c
last=[r for r in rs if r[2]==848];assert len(last)==5
producer=next(r for r in last if r[3]==1)
consumer=next(r for r in last if r[3]==4)
completion=next(r for r in last if r[3]==5)
assert producer[6]==0x0200c27c and producer[1]==15356
assert consumer[29]==0x0200c24c and consumer[21]==0x02005834 and consumer[1]==15359
assert completion[4]==1 and completion[31]==0
inplace=[r for r in rs if r[3]==2]
assert len(inplace)==9 and all(r[4]==0x03007dc0 for r in inplace)
report=dict(result='PASS_BOUNDED_ROTATION_PRODUCER_EVIDENCE',core_sha256=b['core_sha256'],records=45,dropped_records=0,scene=848,first_failed_logic_step=3519,failed_object=hex(consumer[21]),required_key=hex(consumer[29]),captured_producer_key=hex(producer[6]),producer_refresh=producer[1],consumer_refresh=consumer[1],previous_eight_scenes_same_key=True,inplace_observed_destination=hex(inplace[0][4]),same_focused_failure_window_and_audio=True,trace_copy_short_buffer_and_reset_test_executed=True,limits='The trace does not record the requested output matrix or all possible writers. It does not prove unchanged transform reuse, a permitted alias, or the vehicle role. No producer fix is justified yet.',next_dependency='Record requested output matrix bytes and the producing call return, then trace traffic context slot assignment before selecting a safe per-object capture fix.',evidence_sha256={str(q):sha(q) for q in [out/'rotation-trace-build-report.json',out/'rotation-trace-core-test-report.json',out/'probe/background-gap-probe-report.json',out/'probe/rotation-trace.bin',out/'probe/rotation-events.json']},maintained_source_sha256={n:sha(root/n) for n in ['rotation_trace_observer.inc','rotation_trace_core_api.inc','build_rotation_trace_core.py','test_rotation_trace_core.py','probe_rotation_producers.py']},script_sha256=sha(Path(__file__)),game_logic_changed=False,playable_preview_changed=False,full_scene_60fps=False,rough_project_percent=68)
(out/'rotation-trace-milestone-report.json').write_text(json.dumps(report,indent=2))
print(report['result'])
