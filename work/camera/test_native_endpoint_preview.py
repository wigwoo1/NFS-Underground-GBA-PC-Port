"""Paced live native endpoint rendering; deliberately no interpolation claim."""
from pathlib import Path
import subprocess,os,re,csv,json,hashlib
from PIL import Image
p=Path('work/camera').resolve();rom='G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';env=os.environ.copy();env['NF_ENDPOINT_CAPTURE']=str(p/'native-endpoint-live.ppm')
r=subprocess.run([str(p/'native-endpoint-preview.exe'),str(p/'visibility-probe-wide.dll'),rom,str(p.parent/'driving.state'),str(p/'native-endpoint-paced.csv'),'--native-packets','--seconds','3','--window-buffer'],env=env,capture_output=True,text=True,check=True)
values={k:int(v) for k,v in re.findall(r'([a-z_]+)=(\d+)',r.stdout)};assert values['native_endpoint_packets']>0 and values['native_failed']==0 and values['sink_failures']==0 and values['endpoint_only']==1 and values['rendered']>0 and values['simulated']==179
rows=list(csv.DictReader((p/'native-endpoint-paced.csv').open()));ready=[x for x in rows if x['ready']=='1'];assert ready and all(float(x['alpha'])==0 for x in ready)
with Image.open(p/'native-endpoint-live.ppm') as im:
 assert im.size==(3840,2160);rgb=im.convert('RGB');assert any(rgb.getextrema()[i][1]>0 for i in range(3));rgb.resize((960,540)).save(p/'native-endpoint-live-review.png');digest=hashlib.sha256(rgb.tobytes()).hexdigest()
report=dict(result='PASS',values=values,ready_frames=len(ready),all_presented_alpha_zero=True,image_sha256=digest,scope='Live retained-pose native command packets rendered at4K with owned bounds; simulation179refreshes over3seconds. Startup unavailable frames remain. Original logic usesmGBA; no audio/fullscene/smooth60fps gameplay claim.')
(p/'native-endpoint-preview-tests.json').write_text(json.dumps(report,indent=2));print(report)
