"""Verify the initiating producer failure; do not relax the renderer guard."""
from pathlib import Path
import hashlib,json
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');core=base/'NFSUG-pc-traffic-remaining-primary-failure-core';probe=base/'NFSUG-pc-traffic-remaining-primary-failure-probe'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();bp=core/'traffic-remaining-primary-failure-build-report.json';tp=core/'traffic-remaining-primary-failure-core-test-report.json';pp=probe/'diverse-route-report.json'
b=json.loads(bp.read_text());t=json.loads(tp.read_text());p=json.loads(pp.read_text())
assert b['core_sha256']==t['core_sha256']==p['core_sha256']==sha(core/'capture-host.dll')
assert t['result']=='PASS_TRAFFIC_PRIMARY_FAILURE_CORE_PARITY' and t['all_original_pixels_exact'] and t['all_complete_source_bytes_exact'] and t['transfers_balanced']
for n,h in b['maintained_source_sha256'].items():assert sha(source/n)==h,n
for n,h in b['staged_input_sha256'].items():assert sha(core/'source'/n)==h,n
assert b['script_sha256']==sha(source/'build_traffic_remaining_primary_failure_core.py') and t['maintained_test_sha256']==sha(source/'test_traffic_remaining_primary_failure_core.py') and p['script_sha256']==sha(source/'probe_traffic_remaining_primary_failure.py')
assert p['steps']==3630 and p['all3630_original_pixels_exact'] and p['original_clocks_exact'] and p['allocation_lifetimes_balanced']
assert p['short_null_invalid_atomic'] and p['inspection_clock_neutral'] and p['state_reload_clears_diagnostic']
assert [r['step'] for r in p['failures']]==list(range(1,11))+list(range(3610,3615))
prior=json.loads((base/'NFSUG-pc-traffic-remaining-failure-probe/diverse-route-report.json').read_text());assert p['audio_frames']==prior['audio_frames']==2680221 and p['audio_sha256']==prior['audio_sha256']=='426e4f7d8bbc101c767e02e8fdc04a51d31dd22877527db3dbc1f282c7d46547'
w=p['frozen_failure'];assert w[:3]==[0x3146544e,1,640] and len(w)==640
first=w[16:272];last=w[272:400];primary=w[544:640]
assert w[3:9]==[2,0,871,15450,15447,2]
assert first[8]==0x03004770 and first[9]==1 and first[30]==0x02005834 and first[22]==0x0200c24c and first[23]==0xffffffff and first[24]==0
assert first[38:40]==[1,1] and first[165:167]==[1,1]
assert primary[:5]==[0x3150544e,1,128,1,0x08022d44]
assert primary[5]==15448 and primary[16]==15447 and primary[8]==primary[17]==871 and primary[6:8]==primary[18:20]==[2,0]
assert primary[10:12]==[1,1] and primary[13]==first[30] and primary[14]==first[22] and primary[21]==8
assert primary[22]==primary[23]==primary[24]==1 and primary[20]==primary[25]==0 and primary[48:60]==primary[64:76]
assert primary[33]==primary[15] and primary[35]==primary[14]
assert last[10]==0 and last[21]==9 and last[13]==primary[13] and last[16]==primary[16]
report=dict(result='VERIFIED_FIRST_REMAINING_GAP_IS_ONE_REFRESH_PRODUCER_TOKEN_REJECTION',scene=871,logic_step=3610,failed_model_event='0x03004770',original_model_succeeded=True,object=hex(first[30]),required_slot=hex(first[22]),initiating_producer_pc=hex(primary[4]),producer_phase=primary[11],producer_entry_refresh=primary[16],initiating_rejection_refresh=primary[5],model_consume_refresh=first[6],pending_active_at_initiating_failure=True,only_token_mismatch='refresh advanced by exactly one',same_epoch_and_scene=True,same_camera_bytes_at_initiating_failure=True,same_object_index=True,temporary_and_output_addresses_match=True,fresh_model_context_exact=True,followup_inactive_rejection_is_secondary=True,primary_record_prefix_words=96,full_snapshot_record_words=128,scope='First remaining gap only; does not establish that all20 remaining misses share the cause. The second operand is not staged when the token guard fails, so exact downstream products must still be validated by any future bounded handoff.',next_dependency='Sol Medium: implement and test a bounded one-refresh in-flight producer completion while preserving phase/object/slot/camera/source checks, reject stale epochs/scenes/multiple refreshes, then rerun all6000 steps and integrate the live host only after appropriate gates.',runtime_fix_changed=False,playable_package_changed=False,full_scene_60fps=False,rough_project_percent=69,evidence_sha256={str(q):sha(q) for q in [bp,tp,pp,probe/'remaining-failure.bin',probe/'remaining-failure.json',base/'NFSUG-pc-traffic-rotation-draw-camera-core/traffic-draw-camera-milestone-report.json']},script_sha256=sha(Path(__file__)))
(core/'traffic-remaining-primary-milestone-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='evidence_sha256'},indent=2))
