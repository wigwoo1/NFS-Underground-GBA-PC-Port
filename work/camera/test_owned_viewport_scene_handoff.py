import ctypes as C,struct,json
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'viewport-sky-capture-probe.dll').resolve()));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_epoch.restype=C.c_uint64
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
@Sink
def sink(*args):return 1
d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p]
d.nf_owned_graph_closed_read.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
d.nf_owned_graph_closed_viewport.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.POINTER(C.c_uint32),C.c_void_p,C.c_size_t];d.nf_capture_memory_read.argtypes=[C.c_uint,C.c_void_p,C.c_size_t]
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
from dataclasses import replace
from owned_closed_graph import ClosedGraph
from owned_closed_viewport import ClosedViewport
checks=[];retained_viewports=[];retained_scenes=[]
from owned_motion_scene import MotionScene
from types import SimpleNamespace
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/owned-viewport-scene-handoff-20261007');cp.mkdir(exist_ok=True)
d.nf_visibility_capture.argtypes=[C.c_char_p,C.c_uint]
assert d.nf_init(rom,b'') and d.nf_state(b'work/race.state',0);assert d.nf_native_scene_sink(sink,None);assert d.nf_owned_graph_live_enable(1);assert d.nf_visibility_capture(str(cp/'original-builder.bin').encode(),0)
try:
 for i in range(160):
  assert d.nf_frame(1)
  refresh=d.nf_owned_graph_closed_latest()
  if not refresh or any(r['refresh']==refresh for r in checks):continue
  epoch=d.nf_native_scene_epoch();n=C.c_size_t();assert d.nf_owned_graph_closed_read(epoch,refresh,None,0,C.byref(n));raw=C.create_string_buffer(n.value);assert d.nf_owned_graph_closed_read(epoch,refresh,raw,n.value,C.byref(n))
  closed=ClosedGraph.decode(raw.raw);owned=ClosedViewport.capture(d,closed);assert ClosedViewport.decode(owned.encode())==owned
  assert owned.validate_for(closed) is owned;retained_viewports.append(owned)
  scene=MotionScene(closed,SimpleNamespace(epoch=closed.epoch,refresh=closed.refresh,source_refresh=closed.graph.refresh),viewport=owned);assert scene.viewport.validate_for(scene.graph) is owned;retained_scenes.append(scene)
  for wrong in (replace(owned,epoch=owned.epoch+1),replace(owned,refresh=owned.refresh+1),replace(owned,address=owned.address+4)):
   try:wrong.validate_for(closed)
   except ValueError:pass
   else:raise AssertionError('Cross-scene viewport accepted')
  mutable=bytearray(owned.data);copied=replace(owned,data=mutable);mutable[0]^=255;assert copied.data==owned.data
  for malformed in (owned.encode()[:-1],b'BAD!'+owned.encode()[4:]):
   try:ClosedViewport.decode(malformed)
   except ValueError:pass
   else:raise AssertionError('Malformed viewport transport accepted')
  source=struct.unpack_from('<I',raw.raw,44)[0];address=C.c_uint32();view=C.create_string_buffer(16)
  assert d.nf_owned_graph_closed_viewport(epoch,refresh,source,C.byref(address),view,16)
  current=C.create_string_buffer(16);assert d.nf_capture_memory_read(address.value,current,16);live_equal=current.raw==view.raw
  for e,r,s,z in ((epoch+1,refresh,source,16),(epoch,refresh+1,source,16),(epoch,refresh,source+1,16),(epoch,refresh,source,15)):
   assert not d.nf_owned_graph_closed_viewport(e,r,s,C.byref(address),view,z)
  checks.append(dict(refresh=refresh,source=source,address=address.value,viewport=view.raw.hex(),later_live_equal=live_equal,later_live=current.raw.hex()))
 assert checks,'No closed scenes captured'
 assert all(len(v.data)==16 and ClosedViewport.decode(v.encode())==v for v in retained_viewports)
 assert d.nf_owned_graph_live_enable(0);assert not d.nf_owned_graph_closed_viewport(epoch,refresh,source,C.byref(address),view,16)
finally:d.nf_close()
assert all(ClosedViewport.decode(v.encode())==v for v in retained_viewports)
assert all(scene.viewport.validate_for(scene.graph) is scene.viewport for scene in retained_scenes)
raw=(cp/'original-builder.bin').read_bytes();record=88+0x48000;assert len(raw)==2*record
header=struct.unpack_from('<22I',raw);state_address=header[4];ram=raw[88:record]
def retained(address,size):
 offset=address-0x02000000 if address<0x03000000 else 0x40000+address-0x03000000
 return ram[offset:offset+size]
state=retained(state_address,256);projection=retained(struct.unpack_from('<I',state,80)[0],64);address=struct.unpack_from('<I',projection,4)[0];expected=retained(address,16)
match=[r for r in checks if r['source']==header[3]];assert len(match)==1,(header[3],checks)
assert match[0]['address']==address and bytes.fromhex(match[0]['viewport'])==expected
(cp/'oracle.json').write_text(json.dumps(dict(result='PASS',source=header[3],address=address,viewport=expected.hex(),scope='Independent original builder-entry full RAM versus same-source closed viewport; one original scene'),indent=2))
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Actual retained viewport identity/size/disable rejection; later live RAM may mutate and is not capture-time byte oracle'),indent=2));print('PASS',len(checks),'closed viewports')
