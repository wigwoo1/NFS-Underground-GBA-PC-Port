"""A changed retained-image readback must fail before presentation."""
from pathlib import Path
import os,subprocess,json,re
p=Path('work/camera').resolve();root=p.parent
rom='G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
env={k:v for k,v in os.environ.items() if not k.startswith('NF_')}
env.update(NF_PREPARATION_LEAD_US='8000',NF_PREPARE_GPU='1',NF_VERIFY_EARLY_GPU_PIXELS='1',NF_TEST_CORRUPT_EARLY_PIXELS='1',NF_LIVE_HUD='1',NF_LIVE_WORLD_CLASSIFIED='1',NF_LIVE_ROAD_ATTRIBUTES='1',NF_CONTINUOUS_CAMERA='1',NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
report=p/'early-gpu-pixel-rejection-tests.json';report.write_text(json.dumps(dict(result='RUNNING')))
try:
 r=subprocess.run([str(p/'native-endpoint-road-attributes.exe'),str(p/'visibility-probe-wide.dll'),rom,str(root/'driving.state'),str(p/'early-gpu-pixel-rejection.csv'),'--paired-packets','--layer-sync','--scripted-route','--seconds','15','--delay-refreshes','8','--window-buffer'],env=env,text=True,capture_output=True,timeout=25)
 assert r.returncode==19,r.stdout+r.stderr
 assert int(re.search(r'early_gpu_verify_failed=(\d+)',r.stdout)[1])==1
 assert int(re.search(r'early_gpu_verified=(\d+)',r.stdout)[1])==0
 counts={k:int(re.search(k+r'=(\d+)',r.stdout)[1]) for k in ('early_gpu_rendered','early_gpu_presented','early_gpu_discarded','early_gpu_pending')}
 assert counts['early_gpu_discarded']==1 and counts['early_gpu_rendered']==counts['early_gpu_presented']+1 and counts['early_gpu_pending']==0
 value=dict(result='PASS',expected_host_failure=19,changed_readback_bytes=1,host_output=r.stdout,scope='Injected one-byte change in retained-image readback is rejected before accepting the presentation; no altered ROM/state or actual game logic.')
except Exception as error:
 report.write_text(json.dumps(dict(result='FAIL',error=str(error)),indent=2));raise
report.write_text(json.dumps(value,indent=2));print(json.dumps(value,indent=2))
