from pathlib import Path
import ctypes as C,struct,subprocess,json,sys
sys.path.insert(0,'work/pydeps');import numpy as np
p=Path('work/camera').resolve();d=C.CDLL(str(p/'visibility-probe-wide.dll'))
class Section(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t)]
a=d.nf_scene_world_attach_indices;a.argtypes=[Section,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_void_p),C.POINTER(C.c_size_t)];d.nf_scene_packet_free.argtypes=[C.c_void_p]
raw=next((p/'packet-sequence').glob('scene-*.packet')).read_bytes()
def sec(i):
 o,z=struct.unpack_from('<2I',raw,36+i*12);return raw[o:o+z]
model=bytearray(sec(0));mw,mh=struct.unpack_from('<2I',model,16);model[-mw*mh*4:]=bytes([0,255,0,255])*(mw*mh)
world=sec(1);corners,w,h=struct.unpack_from('<3I',world,8);surface=bytearray(world[8:20+corners*40+w*h*4]);indices=bytes((i+i//w)%2 for i in range(w*h))
for i,v in enumerate(indices):surface[12+corners*40+i*4:16+corners*40+i*4]=bytes([0,0,255,255] if v else [255,0,0,255])
world=struct.pack('<2I',0x31444652,1)+surface;wb=C.create_string_buffer(world);ib=C.create_string_buffer(indices);out=C.c_void_p();size=C.c_size_t();assert a(Section(C.addressof(wb),len(world)),0,ib,len(indices),C.byref(out),C.byref(size))
try:tagged=C.string_at(out,size.value)
finally:d.nf_scene_packet_free(out)
colors=struct.unpack('<160H',(p/'zero-gpu-rows.bin').read_bytes())
def render(name,world):
 sections=[model,world,struct.pack('<4I',0x314f464e,2,0,0xffffffff),struct.pack('<3I',0x314c464e,1,0)+sec(3)[-131072:],struct.pack('<2I',0x3149464e,2)+sec(4)[8:28]+sec(4)[-20:]]
 packet=bytearray(raw[:96])
 for i,s in enumerate(sections):
  packet.extend(bytes((-len(packet))%8));struct.pack_into('<2I',packet,36+i*12,len(packet),len(s));packet.extend(s)
 struct.pack_into('<I',packet,8,len(packet));path=p/f'world-zero-{name}.packet';prefix=p/f'world-zero-{name}';path.write_bytes(packet)
 result=subprocess.run([str(p/'zero-snapshot-preview.exe'),str(path),str(prefix),str(p/'zero-gpu-rows.bin')],capture_output=True,text=True);assert result.returncode==0,(result.returncode,result.stdout,result.stderr)
 return np.frombuffer(Path(str(prefix)+'.rgba').read_bytes(),dtype=np.uint8).reshape(2160,3840,4)[::-1].copy()
baseline=render('baseline',world);actual=render('indexed',tagged);mask=np.all(baseline[:,:,:3]==[255,0,0],axis=2);assert mask.sum()>100
expected=baseline.copy()
for y in range(2160):
 c=colors[int((y+.5)/13.5)];expected[y,mask[y]]=[(((c>>(k*5))&31)<<3)|(((c>>(k*5))&31)>>2) for k in range(3)]+[0]
assert np.array_equal(expected,actual),int(np.any(expected!=actual,axis=2).sum())
# Inject failure after packet validation/texture loading: no partial frame output.
failure_prefix=p/'world-zero-forced-failure'
for suffix in ['-0.ppm','.rgba']:
 old=Path(str(failure_prefix)+suffix)
 if old.exists():old.unlink()
failed=subprocess.run([str(p/'zero-snapshot-failure-preview.exe'),str(p/'world-zero-indexed.packet'),str(failure_prefix),str(p/'zero-gpu-rows.bin')],capture_output=True,text=True)
assert failed.returncode==42,(failed.returncode,failed.stdout,failed.stderr)
assert not Path(str(failure_prefix)+'-0.ppm').exists() and not Path(str(failure_prefix)+'.rgba').exists()
legacy=subprocess.run([str(p/'zero-snapshot-failure-preview.exe'),str(p/'world-zero-baseline.packet'),str(p/'world-zero-failure-legacy'),str(p/'zero-gpu-rows.bin')],capture_output=True,text=True)
assert legacy.returncode==0,(legacy.returncode,legacy.stdout,legacy.stderr)
report=dict(result='PASS',exact_rgba_4k_pixels=3840*2160,road_zero_fragments=int(mask.sum()),nonzero_and_model_unchanged=True,forced_gpu_begin_failure_exit=42,partial_frame_not_exported=True,legacy_unaffected_by_indexed_failure=True,scope='Synthetic indexed unlit road GPU overwrite/backdrop coverage and draw failure propagation; original span semantics and live producer pending.')
(p/'world-zero-gpu-tests.json').write_text(json.dumps(report,indent=2));print(report)
