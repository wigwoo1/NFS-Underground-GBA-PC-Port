"""Verify the actual first-multiply rejection before relying on the second candidate."""
from pathlib import Path
import hashlib,json
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');core=base/'NFSUG-pc-traffic-refresh-primary-failure-core';probe=base/'NFSUG-pc-traffic-refresh-primary-failure-probe';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((core/'traffic-refresh-primary-failure-build-report.json').read_text());t=json.loads((core/'traffic-refresh-primary-failure-core-test-report.json').read_text());r=json.loads((probe/'diverse-route-report.json').read_text());a=json.loads((probe/'primary-rejection-analysis.json').read_text())
assert b['core_sha256']==t['core_sha256']==r['core_sha256']==sha(core/'capture-host.dll')
for n,h in b['maintained_source_sha256'].items():assert sha(source/n)==h,n
assert t['all_original_pixels_exact'] and t['all_complete_source_bytes_exact'] and t['transfers_balanced']
assert r['steps']==3690 and r['all3690_original_pixels_exact'] and r['original_clocks_exact'] and r['allocation_lifetimes_balanced'] and r['short_null_invalid_atomic'] and r['inspection_clock_neutral'] and r['state_reload_clears_diagnostic']
assert [f['step'] for f in r['failures']]==list(range(1,11))+list(range(3667,3671)) and r['audio_frames']==2724520 and r['audio_sha256']=='4b49721143d54c2e36d57a1eb3f34636483caa9a684c5e7b3032982c644fbd70'
w=r['frozen_failure'];f=w[16:272];p=w[544:640];last=w[272:400]
assert w[3:9]==[2,0,885,15507,15504,3] and f[8:10]==[0x03004770,1] and f[30]==0x020058d8 and f[22]==0x0200c24c and f[23]==0xffffffff
assert f[38:40]==[1,1] and f[165:167]==[1,1]
assert p[:5]==[0x3150544e,1,128,2,0x08022d38] and p[10:12]==[1,0] and p[5]==15505 and p[16]==15504 and p[21]==8
assert p[8]==p[17]==885 and p[6:8]==p[18:20]==[2,0] and p[13]==f[30] and p[14]==f[22]
assert p[22]==p[23]==p[24]==1 and p[20]==p[25] and p[48:60]==p[64:76] and p[34]==p[12] and p[15]==0
assert last[10]==0 and last[21]==9 and last[13]==p[13]
assert a['snapshot_sha256']==sha(probe/'remaining-failure.bin') and a['script_sha256']==sha(source/'decode_traffic_refresh_primary_failure.py')
report=dict(result='VERIFIED_FIRST_REMAINING_CROSSING_IS_BEFORE_FIRST_MULTIPLY',scene=885,step=3667,primary_pc='0x08022d38',phase=0,entry_refresh=15504,rejection_refresh=15505,same_epoch_scene_camera_object_index=True,first_multiply_camera_argument_matches=True,original_model_success_and_context_exact=True,only_original_token_mismatch='one refresh',followup_inactive_rejection_secondary=True,no_prior_token_adoption_possible_at_phase0=True,original3690_pixels_audio_clocks_exact=True,inspection_reset_invalid_guards_passed=True,diagnostic_core_sha256=b['core_sha256'],runtime_fix_changed=False,full_scene_60fps=False,receipts={str(p):sha(p) for p in [core/'traffic-refresh-primary-failure-build-report.json',core/'traffic-refresh-primary-failure-core-test-report.json',probe/'diverse-route-report.json',probe/'remaining-failure.bin',probe/'primary-rejection-analysis.json']},script_sha256=sha(Path(__file__)))
(probe/'first-stage-evidence-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='receipts'},indent=2))
