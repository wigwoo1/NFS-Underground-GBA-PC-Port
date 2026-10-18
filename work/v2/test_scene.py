from pathlib import Path
import ctypes as C,json,hashlib,time,struct
r=Path('work').resolve();d=C.CDLL(str(r/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_pixels.restype=C.c_void_p;d.nf_read.restype=C.c_uint32;d.nf_scene.restype=C.c_void_p
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
assert d.nf_init(rom,b'');runs=[]
for enabled in [0,1]:
 assert d.nf_state(str(r/'race.state').encode(),0);d.nf_speed(1);d.nf_scene_enable(enabled)
 digest=hashlib.sha256();t=time.perf_counter();counts=[]
 for i in range(600):
  d.nf_frame(1 if i<400 else 17)
  digest.update(C.string_at(d.nf_pixels(),240*160*4))
  if i%60==59:
   ptr=d.nf_read(0x30000fc,4);idx=d.nf_read(0x3000068,4);car=ptr+idx*0xa4
   digest.update(struct.pack('<6I',*[d.nf_read(car+k,4) for k in [12,20,24,32,44,140]]))
  n=C.c_int();d.nf_scene(C.byref(n));counts.append(n.value)
 d.nf_state(str(r/'v2'/f'equivalence-{enabled}.state').encode(),1)
 runs.append({'capture_enabled':enabled,'frames':600,'frame_and_vehicle_sha256':digest.hexdigest(),'max_polygons':max(counts),'seconds':time.perf_counter()-t})
assert runs[0]['frame_and_vehicle_sha256']==runs[1]['frame_and_vehicle_sha256']
assert d.nf_state(str(r/'race.state').encode(),0);n=C.c_int();d.nf_scene(C.byref(n));assert n.value==0
result={'result':'PASS','scope':'600 identical input frames with scene capture disabled/enabled; every original framebuffer and sampled vehicle state matches; loading a state clears captured geometry. Does not prove GPU pixel equivalence or 60 fps.','runs':runs,'load_clears_geometry':True}
(r/'v2/scene-tests.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));d.nf_close()
