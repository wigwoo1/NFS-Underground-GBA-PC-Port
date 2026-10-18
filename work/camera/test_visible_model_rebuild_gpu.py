"""Visible 4K fullscene parity after owned-source scenery reconstruction."""
import sys,json,struct,ctypes as C
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_motion_scene import MotionScene
from owned_model_builder_inputs import OwnedModelBuilders
from owned_model_record_builder import ModelRecordBuilder
from owned_wall_region_candidates import regions
from owned_motion_pairs import records
from owned_sampled_supplemental_frame import encode
rpath=Path(sys.argv[1]);report=json.loads(rpath.read_text());coverage=json.loads(rpath.with_suffix('.model-coverage.json').read_text());visible={x['refresh']:x for x in coverage['scenes'] if x['combined_changed_pixels']}
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();builder=ModelRecordBuilder(rom);table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072])
d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3);checks=[]
try:
 for item in report['model_scene_captures']:
  if item['refresh'] not in visible:continue
  frame=Path(item['frame']).read_bytes();graph=ClosedGraph.decode(Path(item['graph']).read_bytes());supplements=ClosedSupplements.decode(Path(item['supplements']).read_bytes(),graph,rom);scene=MotionScene(graph,supplements,OwnedModelBuilders(Path(item['builders']).read_bytes()))
  rebuilt=builder.rebuild(scene,regions(graph.graph,table),frame);rows=records(frame)['records'];geometry=b''.join(encode(rebuilt.get(i,row)) for i,row in enumerate(rows));h=list(struct.unpack_from('<6I2Q',frame));tail=frame[40+h[2]:];h[2]=len(geometry);adapted=struct.pack('<6I2Q',*h)+geometry+tail
  assert d.nf_owned_gpu_draw(frame,len(frame))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0;expected=rgb.raw
  assert d.nf_owned_gpu_draw(adapted,len(adapted))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==expected
  assert len(rebuilt)==visible[item['refresh']]['scenery_records']
  checks.append(dict(refresh=item['refresh'],rebuilt_models=len(rebuilt),visible_scenery_pixels=visible[item['refresh']]['combined_changed_pixels'],pixels_exact=True))
finally:assert d.nf_owned_gpu_close()
assert len(checks)==7
out=dict(result='PASS_VISIBLE_SOURCE_REBUILT_SCENERY_4K',checks=checks,scope='Seven covered fullscene endpoints; fractional motion/activation sampling, live cadence, physical Xbox unverified.')
rpath.with_suffix('.visible-model-rebuild.json').write_text(json.dumps(out,indent=2));print(out)
