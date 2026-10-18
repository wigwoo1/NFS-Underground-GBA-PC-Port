"""Measure visible model contribution in owned later scenes, without screen matching."""
import sys,json,ctypes as C,struct
from pathlib import Path
import numpy as np
from owned_closed_graph import ClosedGraph
from owned_motion_pairs import records
from owned_sampled_supplemental_frame import encode
report_path=Path(sys.argv[1]);report=json.loads(report_path.read_text());captures=report['model_scene_captures'];rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3);results=[]
def draw(frame):
 assert d.nf_owned_gpu_draw(frame,len(frame))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0
 return np.frombuffer(rgb.raw,dtype=np.uint8).reshape(-1,3)
try:
 for item in captures:
  frame=Path(item['frame']).read_bytes();graph=ClosedGraph.decode(Path(item['graph']).read_bytes());graph.match_frame(frame);rows=records(frame)['records'];base=struct.unpack_from('<I',graph.graph.context,124)[0]
  descriptors={rom[base-0x08000000+(m-1)*40:base-0x08000000+m*40]:m for m in range(31,37)}
  model_indices={i:descriptors[bytes(row['blocks'][1])] for i,row in enumerate(rows) if row['kind']==3 and bytes(row['blocks'][1]) in descriptors}
  header=list(struct.unpack_from('<6I2Q',frame));tail=frame[40+header[2]:];expected=draw(frame)
  def omitted(indices):
   geometry=b''.join(encode(row) for i,row in enumerate(rows) if i not in indices);h=header.copy();h[2]=len(geometry)
   return int(np.count_nonzero(np.any(draw(struct.pack('<6I2Q',*h)+geometry+tail)!=expected,axis=1)))
  combined=omitted(set(model_indices)) if model_indices else 0
  individual=[dict(record_index=i,model=m,changed_pixels=omitted({i})) for i,m in model_indices.items()] if combined else []
  results.append(dict(refresh=item['refresh'],scenery_records=len(model_indices),combined_changed_pixels=combined,individual=individual))
finally:assert d.nf_owned_gpu_close()
out=dict(result='MEASURED_4K_SCENERY_COVERAGE',scenes=results,visible_scenes=sum(x['combined_changed_pixels']>0 for x in results),scope='Omission coverage only; no source-rebuild fidelity or fractional motion claim.')
report_path.with_suffix('.model-coverage.json').write_text(json.dumps(out,indent=2));print(out)
