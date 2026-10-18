from pathlib import Path
import os,sys,subprocess,json
from scene_batches import batches
root=Path('work/camera');folder=root/'packet-sequence';folder.mkdir(exist_ok=True)
count=len(list(batches(root/'world.bin')));paths=[];sizes=[]
def export(serial):
 env=dict(os.environ,NF_REPLAY_SCENE=str(serial))
 for script in ['export_model_preview.py','export_wall_preview.py','export_draw_order.py','export_wall_lighting.py','export_scene_packet.py']:
  result=subprocess.run([sys.executable,str(root/script)],env=env,capture_output=True,text=True)
  if result.returncode:raise RuntimeError(f'Scene {serial}: {script}\n'+result.stdout+result.stderr)
try:
 for serial in range(count):
  export(serial);data=(root/'scene-packet.bin').read_bytes();path=folder/f'scene-{serial:03}.packet';path.write_bytes(data);paths.append(path.as_posix());sizes.append(len(data))
finally:export(10)
(root/'packet-sequence.txt').write_text('\n'.join(paths)+'\n')
report={'scenes':count,'total_bytes':sum(sizes),'max_packet_bytes':max(sizes),'scope':'Supported scene packets from one prerecorded driving capture, not live extraction.'}
(root/'packet-sequence-input.json').write_text(json.dumps(report,indent=2));print(report)
