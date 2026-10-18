"""Repeatable offline coverage; never launches or modifies the playable host."""
from pathlib import Path
import subprocess,sys,os,json,hashlib,re
from PIL import Image
root=Path('work/camera');scenes=[0,20,30,40];report=[];images=[]
startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
def export(scene):
 env=dict(os.environ,NF_REPLAY_SCENE=str(scene))
 for name in ['export_model_preview.py','export_wall_preview.py','export_draw_order.py','export_wall_lighting.py']:
  result=subprocess.run([sys.executable,str(root/name)],env=env,capture_output=True,text=True)
  if result.returncode:raise RuntimeError(name+'\n'+result.stdout+result.stderr)
try:
 for serial in scenes:
  export(serial);prefix=root/f'lighting-scene-{serial}'
  result=subprocess.run([str((root/'lit-preview.exe').resolve()),str(root/'model-preview.bin'),str(prefix),str(root/'empty-world-preview.bin'),str(root/'wall-scene-preview.bin'),str(root/'draw-order.bin'),str(root/'wall-lighting.bin')],startupinfo=startup,capture_output=True,text=True)
  assert result.returncode==0,(serial,result.returncode,result.stderr)
  counters=re.findall(r'frame=(\d+) phase=([\d.]+) faces=(\d+) lit=(\d+) lighting_fallback=(\d+)',result.stdout)
  assert len(counters)==5 and all(int(row[4])==0 for row in counters),(serial,result.stdout)
  hashes=[]
  for phase in range(5):
   path=Path(f'{prefix}-{phase}.ppm');im=Image.open(path);assert im.size==(3840,2160)
   hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())
  assert len(set(hashes))==5,serial
  images.append(Image.open(f'{prefix}-2.ppm').resize((640,360)))
  report.append({'scene':serial,'frames':5,'lighting_applications':int(counters[-1][3]),'lighting_fallbacks':0,'hashes':hashes})
finally:
 export(10)
montage=Image.new('RGB',(1280,720))
for index,im in enumerate(images):montage.paste(im,((index%2)*640,(index//2)*360))
montage.save(root/'lighting-coverage.png')
(root/'lighting-coverage-tests.json').write_text(json.dumps({'result':'PASS','scenes':report,'scope':'Four scenes from one driving capture, twenty offscreen 4K phases. No realtime pacing or complete gameplay coverage.'},indent=2))
print('PASS: four scenes, twenty distinct 4K phases, zero lighting fallbacks. Private inputs restored to scene 10.')
