"""4K full-scene GPU comparison with independently reconstructed car records."""
from pathlib import Path
import ctypes as C,struct,json,hashlib
from owned_model_scene_packet import ModelScenePacket
from owned_scene_bundle import SceneBundle
from owned_scene_model_binding import attach_meshes
from owned_scene_gpu_model import encode,palette
from owned_motion_pairs import records
p=Path('work/camera');d=C.CDLL(str((p/'owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3);checks=[]
poses=(p/'owned-object-poses.bin').read_bytes();textures=(p/'owned-object-textures.bin').read_bytes();palettes=(p/'owned-object-palettes.bin').read_bytes();assets={(7,0):(p/'model-assets/7-0.nma').read_bytes()}
def render(frame):
 assert d.nf_owned_gpu_draw(frame,len(frame))==0
 assert d.nf_owned_gpu_read(rgb,len(rgb))==0
 return rgb.raw
try:
 for file,refresh in zip(sorted((p/'scene-bundles').glob('*.nsb')),(8758,8762,8766,8769,8773,8776,8780)):
  packet=ModelScenePacket.decode((p/'model-scene-packets'/(file.stem+'.nsc')).read_bytes());model_records=packet.gpu_records();frame=(p/f'motion-actual-scanline-assets/{refresh}-native-complete-frame.bin').read_bytes();header=list(struct.unpack_from('<6I2Q',frame));parsed=records(frame);geometry=[];index=0
  for row in parsed['records']:
   if row['kind']==3:
    geometry.append(model_records[index]);index+=1
   else:geometry.append(struct.pack('<4I',0x3147534e,row['kind'],row['context'],12)+b''.join(struct.pack('<I',len(b))+bytes(b) for b in row['blocks']))
  assert index==len(model_records);g=b''.join(geometry);tail=frame[40+header[2]:];header[2]=len(g);adapted=struct.pack('<6I2Q',*header)+g+tail
  expected=render(frame);actual=render(adapted);assert actual==expected,(file.name,sum(a!=b for a,b in zip(actual,expected)))
  checks.append(dict(scene=file.name,refresh=refresh,pixels_exact=3840*2160,rgb_sha256=hashlib.sha256(actual).hexdigest()))
finally:assert d.nf_owned_gpu_close()
r=dict(result='PASS_RECONSTRUCTED_MODEL_FULL_FRAME_4K_GPU_PARITY',checks=checks,scope='Car records reconstructed from scene assets; roads/walls/HUD retained captured. Diagnostic GPU replay, not live unified scene or60fps gameplay proof.')
(p/'owned-scene-model-gpu-replay.json').write_text(json.dumps(r,indent=2));print(r)
