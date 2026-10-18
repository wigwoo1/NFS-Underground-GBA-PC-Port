import ctypes as C,csv,json,struct,hashlib
from pathlib import Path
p=Path(__file__).resolve().parent
prefix=p/'prototype-runs/threaded-prepared-2d9f8b417e1943be80cb86a65dc8f12d'
session=json.loads(Path(str(prefix)+'-session.json').read_text(encoding='utf-8-sig'))
for name in ('rom','state'):assert hashlib.sha256(Path(session[name]).read_bytes()).hexdigest()==session[name+'_sha256'].lower()
P=C.c_void_p;U=C.c_uint32;Z=C.c_size_t
crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p]
assert crt._putenv_s(b'NF_CAPTURE_MODEL_VIEWS',b'1')==0
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_live_visibility_enable.argtypes=[P,Z,Z];d.nf_scene_packet_free.argtypes=[P]
Sink=C.CFUNCTYPE(C.c_int,P,C.c_uint64,P,Z);latest={}
@Sink
def sink(ctx,epoch,data,size):latest.update(epoch=epoch,serial=struct.unpack_from('<I',C.string_at(data,20),16)[0]);return 1
d.nf_native_scene_sink.argtypes=[Sink,P]
d.nf_live_completed_draw_scene_packet.argtypes=[C.c_uint64,U,P,P,P,U,P]
def get(enabled):
 assert crt._putenv_s(b'NF_CAPTURE_WALL_OUTPUT_INDICES',b'1' if enabled else b'')==0
 out=P();size=Z();poses=C.create_string_buffer(8064);count=U()
 assert d.nf_live_completed_draw_scene_packet(latest['epoch'],latest['serial'],C.byref(out),C.byref(size),poses,144,C.byref(count))
 try:raw=C.string_at(out,size.value)
 finally:d.nf_scene_packet_free(out)
 return {t:raw[o:o+n] for t,o,n in (struct.unpack_from('<3I',raw,32+j*12) for j in range(5))},poses.raw[:count.value*56]
assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
try:
 assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
 rom=Path(session['rom']).read_bytes();assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024)
 d.nf_live_surface_audit_enable(1)
 for index,row in enumerate(csv.DictReader(Path(str(prefix)+'-input.csv').open())):
  d.nf_frame(int(row['keys']))
  if index==46:break
 old,oc=get(False);new,nc=get(True)
 assert oc==nc and all(old[t]==new[t] for t in (1,3,4,5))
 world=old[2];count=struct.unpack_from('<I',world,4)[0];at=8
 for i in range(count):
  corners,w,h=struct.unpack_from('<3I',world,at);at+=12+corners*40+w*h*4
 assert world[:at]==new[2][:at]
 def metadata(raw):
  cursor=at;assert raw[cursor:cursor+4]==b'NWI1';cursor+=8;items=[]
  for i in range(count):
   mode,size=struct.unpack_from('<2I',raw,cursor);cursor+=8;items.append((mode,raw[cursor:cursor+size]));cursor+=size
  assert cursor==len(raw);return items
 walls=0;bytes_checked=0
 for (mode,a),(newmode,b) in zip(metadata(world),metadata(new[2])):
  if mode in (2,3):
   assert newmode==(7 if mode==2 else 8) and len(b)==len(a)*2 and b[:len(a)]==a
   indices=b[len(a):];assert all((state==2)==(value!=0) for state,value in zip(a,indices));walls+=1;bytes_checked+=len(indices)
  else:assert mode==newmode and a==b
 assert walls
finally:d.nf_close();crt._putenv_s(b'NF_CAPTURE_WALL_OUTPUT_INDICES',b'')
report=dict(result='PASS',serial=latest['serial'],walls=walls,output_index_bytes=bytes_checked,geometry_order_lighting_models_cameras_exact=True,scope='Actual ownedroot exactpacket opt-in wallmetadata versuslegacy; no independent original shades/GPUscene/timing proof.')
(p/'live-wall-index-metadata-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
