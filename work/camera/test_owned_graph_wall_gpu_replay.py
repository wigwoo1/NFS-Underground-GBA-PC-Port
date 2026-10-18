"""4K parity for owned wall source/material substitution; captured dispatch retained."""
from pathlib import Path
import ctypes as C,struct,json,hashlib
from owned_graph_packet import GraphPacket
from owned_scene_bundle import SceneBundle
from owned_graph_wall_sources import wall_sources,supplemental_wall_sources
from owned_motion_pairs import records
from owned_wall_region_candidates import source_flags
from owned_scene_gpu_wall import gpu_records,supplemental_gpu_records
p=Path('work/camera');d=C.CDLL(str((p/'owned-world-gpu.dll').resolve()))
d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t]
rgb=C.create_string_buffer(3840*2160*3);checks=[]
def render(frame):
 code=d.nf_owned_gpu_draw(frame,len(frame));assert code==0,code
 assert d.nf_owned_gpu_read(rgb,len(rgb))==0
 return rgb.raw
try:
 for src,dst in zip((8754,8758,8762,8765,8769,8772,8776),(8758,8762,8766,8769,8773,8776,8780)):
  graph=GraphPacket.decode((p/f'graph-packets/{src}.ngp').read_bytes())
  sources=wall_sources(graph)+supplemental_wall_sources(SceneBundle.decode((p/f'scene-bundles/{src}.nsb').read_bytes()))
  regenerated=dict(gpu_records(graph,struct.unpack("<32768I",(p/"road-correction-reciprocal.bin").read_bytes()[:131072])))
  regenerated.update(supplemental_gpu_records(SceneBundle.decode((p/f'scene-bundles/{src}.nsb').read_bytes()),struct.unpack("<32768I",(p/"road-correction-reciprocal.bin").read_bytes()[:131072])))
  frame=(p/f'motion-actual-scanline-assets/{dst}-native-complete-frame.bin').read_bytes();header=list(struct.unpack_from('<6I2Q',frame));geometry=[];count=0
  for row in records(frame)['records']:
   b=[bytes(x) for x in row['blocks']]
   if row['kind']==2 and b[0] in regenerated:
    geometry.append(regenerated.pop(b[0]));count+=1;continue
   geometry.append(struct.pack('<4I',0x3147534e,row['kind'],row['context'],12)+b''.join(struct.pack('<I',len(x))+x for x in b))
  assert not regenerated
  g=b''.join(geometry);tail=frame[40+header[2]:];header[2]=len(g);adapted=struct.pack('<6I2Q',*header)+g+tail
  expected=render(frame);actual=render(adapted);assert actual==expected,(dst,sum(a!=b for a,b in zip(actual,expected)))
  checks.append(dict(refresh=dst,walls=count,pixels_exact=3840*2160,rgb_sha256=hashlib.sha256(actual).hexdigest()))
finally:assert d.nf_owned_gpu_close()
r=dict(result='PASS_REGENERATED_GRAPH_WALL_4K_GPU_PARITY',checks=checks,scope='Graph and supplemental wall records regenerated from independently selected edges and owned camera/material/clip/palette/scratch. Captured road/model/HUD and cross-kind interleaving retained. Diagnostic replay, not full-scene ownership or60fps proof.')
(p/'owned-graph-wall-gpu-replay.json').write_text(json.dumps(r,indent=2));print(r)




