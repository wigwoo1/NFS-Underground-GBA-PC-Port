"""4K parity for owned wall source/material substitution; captured dispatch retained."""
from pathlib import Path
import ctypes as C,struct,json,hashlib
from owned_graph_packet import GraphPacket
from owned_scene_bundle import SceneBundle
from owned_graph_wall_sources import wall_sources,supplemental_wall_sources
from owned_motion_pairs import records
from owned_wall_region_candidates import source_flags
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
  frame=(p/f'motion-actual-scanline-assets/{dst}-native-complete-frame.bin').read_bytes();header=list(struct.unpack_from('<6I2Q',frame));geometry=[];count=0
  for row in records(frame)['records']:
   b=[bytes(x) for x in row['blocks']]
   if row['kind']==2:
    matches=[w for w in sources if w.vertices==b[0] and w.offsets==b[1]]
    assert matches,'Missing raw edge identity'
    w=matches[0];assert all(x==w for x in matches),'Ambiguous raw edge'
    b[0]=w.vertices;b[1]=w.offsets;b[2]=w.animation
    b[3]=graph.context[256:304];context=bytearray(b[11]);struct.pack_into("<I",context,256,source_flags(w));b[11]=bytes(context)
    material=bytearray(48);struct.pack_into('<HH',material,36,w.shift,w.height);b[4]=bytes(material);assert len(w.texture)<=65536;b[8]=w.texture.ljust(65536,b"\x00");count+=1
   geometry.append(struct.pack('<4I',0x3147534e,row['kind'],row['context'],12)+b''.join(struct.pack('<I',len(x))+x for x in b))
  g=b''.join(geometry);tail=frame[40+header[2]:];header[2]=len(g);adapted=struct.pack('<6I2Q',*header)+g+tail
  expected=render(frame);actual=render(adapted);assert actual==expected,(dst,sum(a!=b for a,b in zip(actual,expected)))
  checks.append(dict(refresh=dst,walls=count,pixels_exact=3840*2160,rgb_sha256=hashlib.sha256(actual).hexdigest()))
finally:assert d.nf_owned_gpu_close()
r=dict(result='PASS_OWNED_WALL_SOURCE_MATERIAL_4K_GPU_PARITY',checks=checks,scope='Wall raw vertices, offsets, animation and complete texture reconstructed from graph/supplements; material dimensions canonicalized. Camera and flags derived from owned graph/raw wall source. Captured dispatch, clip and palette retained. Diagnostic replay, not full-scene ownership or60fps proof.')
(p/'owned-wall-source-gpu-replay.json').write_text(json.dumps(r,indent=2));print(r)




