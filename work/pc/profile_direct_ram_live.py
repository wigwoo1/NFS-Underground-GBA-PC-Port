"""Paired real-time live profile, confined to the candidate staging folder."""
from pathlib import Path
import os,subprocess,json,hashlib,shutil
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-direct-ram-live-tests';candidate=base/'NFSUG-pc-direct-ram-core-tests';baseline=base/'NFSUG-pc-owned-assembly-core-tests/capture-host.dll';env=dict(os.environ)
for key in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TEST_DIRECT_CAPTURE_RAM','NF_TEST_DIRECT_CAPTURE_ROM','NF_TEST_VERIFY_CAPTURE_RAM','NF_TEST_VERIFY_CAPTURE_ROM']:env.pop(key,None)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((candidate/'owned-core-test-report.json').read_text());assert receipt['core_sha256']==sha(candidate/'capture-host.dll') and receipt['baseline_core_sha256']==sha(baseline)
live=json.loads((out/'live-test-report.json').read_text());assert live['core_sha256']==sha(candidate/'capture-host.dll') and live['exe_sha256']==sha(out/'NFSUG-Source-Native-Preview.exe')
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in [rom,state]};cases={}
try:
 for name,core in [('bus-ram',baseline),('direct-ram',candidate/'capture-host.dll')]:
  shutil.copy2(core,out/'capture-host.dll');cmd=[str(out/'NFSUG-Source-Native-Preview.exe'),'--rom',str(rom),'--state',str(state),'--hidden','--script','--frames','1200','--report',str(out/f'profile-{name}.json'),'--audio-dump',str(out/f'profile-{name}.pcm')]
  subprocess.run(cmd,env=env,check=True,timeout=90);r=json.loads((out/f'profile-{name}.json').read_text())
  assert r['logic_frames']==1200 and r['timing_errors']==0 and r['present_failures']==0 and r['prepare_failures']==0 and r['native_renders']>0 and r['audio_dropped_frames']==0
  assert sha(out/f'profile-{name}.pcm')=='84d8e27f4ecdf97eff82a279523a546331d31c7c03b2b6f5723462d485ec08be';cases[name]=r
  print(name,r['elapsed_seconds'],r['phases']['core_step'],flush=True)
finally:shutil.copy2(candidate/'capture-host.dll',out/'capture-host.dll')
assert before=={str(p):sha(p) for p in [rom,state]}
r=dict(result='PASS_DIRECT_RAM_LIVE_PROFILE_PCM_TIMING_COUNTS',cases=cases,ideal_seconds=1200*280896/16777216,baseline_core_sha256=sha(baseline),core_sha256=sha(out/'capture-host.dll'),exe_sha256=sha(out/'NFSUG-Source-Native-Preview.exe'),parity_receipt_sha256=sha(candidate/'owned-core-test-report.json'),live_test_receipt_sha256=sha(out/'live-test-report.json'),script_sha256=sha(Path(__file__)),rom_state_sha256=before,full_scene_60fps=False,limit='Single paired 1200-step run; CPU submission metrics only. Full PCM equality, no independent 1200-frame pixel oracle. No universal pacing or maximum-latency claim.')
(out/'direct-ram-profile-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='cases'},indent=2))
