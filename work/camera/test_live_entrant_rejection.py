"""Research failure injection: reject candidates before and after composition."""
from pathlib import Path
import os, subprocess, json, re
from PIL import Image, ImageChops
p=Path(__file__).resolve().parent
env=os.environ.copy()
for key in ('NF_LIVE_ENTRANTS','NF_ENTRANT_FAULT','NF_ENTRANT_EXPORT','NF_ENTRANT_LIVE_CAPTURE','NF_LIVE_CLIP_EXPORT'):
    env.pop(key,None)
results=[]
baseline=None
for mode in ('disabled','truncated','after-compose','state-conflict','duplicate-peer','region-conflict','enabled'):
    runenv=env.copy()
    if mode!='disabled':runenv['NF_LIVE_ENTRANTS']='1'
    if mode in ('truncated','after-compose','state-conflict','duplicate-peer','region-conflict'):runenv['NF_ENTRANT_FAULT']=mode
    prefix=p/f'entrant-rejection-{mode}'
    run=subprocess.run([str(p/'live-ordered-preview.exe'),str(p/'visibility-probe.dll'),
        'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba',
        'work/driving.state',str(prefix)+'.csv',str(prefix),'--sampled-clips','--reload'],
        env=runenv,check=True,capture_output=True,text=True)
    assert 'retained_rebuilt=96 retained_failed=0' in run.stdout
    assert 'result=0 live_packets=96 rendered=342' in run.stdout
    assert 'render_pose_expired=0' in run.stdout
    expected=6 if mode=='enabled' else 0
    assert f'entrant_live_applied={expected} released={expected}' in run.stdout
    assert f'entrant_fallback={6-expected}' in run.stdout
    packets=re.findall(r'entrant_packet scene=\d+ composed=(\d+) bytes=(\d+)',run.stdout)
    if mode in ('truncated','after-compose'):
        assert len(packets)==6 and all(int(ok)==0 for ok,size in packets)
        assert all((int(size)>0)==(mode=='after-compose') for ok,size in packets)
    if mode in ('state-conflict','duplicate-peer','region-conflict'):
        assert not packets
        states=re.findall(r'entrant_state scene=\d+ state=\d+ accepted=(\d+)',run.stdout)
        assert states==['0']*6
    with Image.open(str(prefix)+'-0.ppm') as image:
        if baseline is None:baseline=image.copy()
        else:assert ImageChops.difference(baseline,image).getbbox() is None
    results.append(dict(mode=mode,applied=expected,released=expected,fallbacks=6-expected,log=run.stdout))
report=dict(result='PASS',cases=results,scope='Unpaced research rejection runs and final-frame recovery. Release counters cover transferred frames, not allocator-level leak detection; entrant fallback pixels are not captured.')
(p/'live-entrant-rejection-tests.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='cases'}))

