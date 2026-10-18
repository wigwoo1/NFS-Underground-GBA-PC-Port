"""Compare equal-pose renders on either side of retained-scene replacement."""
from pathlib import Path
import os,sys,subprocess,json
from PIL import Image,ImageChops
from scene_batches import batches
from surface_identity import wall_identity
root=Path('work/camera');scenes=list(batches(root/'world.bin'));report=[];largest=(-1,None)
startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
def export(serial):
 env=dict(os.environ,NF_REPLAY_SCENE=str(serial))
 for script in ['export_model_preview.py','export_wall_preview.py','export_draw_order.py','export_wall_lighting.py']:
  p=subprocess.run([sys.executable,str(root/script)],env=env,capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
 return (root/'model-preview.bin').read_bytes()[48:272]
def render(phase):
 prefix=root/f'handoff-phase-{phase}';env=dict(os.environ,NF_PREVIEW_PHASE=str(phase))
 p=subprocess.run([str((root/'lit-preview.exe').resolve()),str(root/'model-preview.bin'),str(prefix),str(root/'empty-world-preview.bin'),str(root/'wall-scene-preview.bin'),str(root/'draw-order.bin'),str(root/'wall-lighting.bin')],env=env,startupinfo=startup,capture_output=True,text=True)
 assert p.returncode==0,p.stdout+p.stderr
 return Image.open(f'{prefix}-{phase}.ppm').copy()
def surfaces(scene):
 result=set()
 for e in scene['events']:
  b=e['blocks']
  if e['pc']==0x03000304:result.add(wall_identity(e))
  elif e['pc']==0x030032f0:result.add(('road',b[1][0],b[4][0]))
 return result
def material_changes(before,after):
 def walls(scene):
  found={}
  for e in scene['events']:
   if e['pc']==0x03000304:found.setdefault(e['blocks'][5][0],[]).append(e)
  return found
 a,b=walls(before),walls(after);changes=[]
 for key in a.keys()&b.keys():
  if len(a[key])!=1 or len(b[key])!=1:continue
  x,y=a[key][0]['blocks'],b[key][0]['blocks']
  if x[4][0]!=y[4][0]:changes.append({'source':hex(key),'before_material':hex(x[4][0]),'after_material':hex(y[4][0]),'before_texture':hex(x[66][0]),'after_texture':hex(y[66][0]),'source_record_unchanged':x[5][1]==y[5][1]})
 return changes
try:
 for serial in [0,9,19,29,39]:
  before_pose=export(serial);before=render(4)
  after_pose=export(serial+1);after=render(0)
  assert before_pose[56:112]==after_pose[:56] and before_pose[168:224]==after_pose[112:168],serial
  difference=ImageChops.difference(before,after);changed=sum(pixel!=(0,0,0) for pixel in difference.get_flattened_data())
  a=surfaces(scenes[serial]);b=surfaces(scenes[serial+1])
  report.append({'from_scene':serial,'to_scene':serial+1,'identical_camera_and_object_pose':True,'changed_pixels':changed,'surfaces_entering':len(b-a),'surfaces_leaving':len(a-b),'wall_material_changes':material_changes(scenes[serial],scenes[serial+1])})
  if changed>largest[0]:
   im=Image.new('RGB',(1280,360));im.paste(before.resize((640,360)),(0,0));im.paste(after.resize((640,360)),(640,0));largest=(changed,im)
finally:export(10)
largest[1].save(root/'handoff-inspect.png')
result={'comparison_completed':True,'boundaries':report,'scope':'Equal-pose diagnostic. Changed pixels reveal scene replacement differences; this is not a passing continuity claim.'}
(root/'scene-handoff-tests.json').write_text(json.dumps(result,indent=2));print(result)
