"""Actual original replay verifies cache ownership, expiry and epoch rejection."""
import ctypes as C,struct,json,uuid
from pathlib import Path
p=Path(__file__).resolve().parent;P=C.c_void_p;U=C.c_uint32;Z=C.c_size_t
crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p]
for k in ['NF_CAPTURE_MODEL_VIEWS','NF_TEST_EXACT_SCENE_CACHE']:assert crt._putenv_s(k.encode(),b'1')==0
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p/'prototype-runs/menu-navigation/quick-1-release.state'
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_live_visibility_enable.argtypes=[P,Z,Z];d.nf_dump.argtypes=[C.c_char_p,U,U]
Sink=C.CFUNCTYPE(C.c_int,P,C.c_uint64,P,Z);d.nf_native_scene_sink.argtypes=[Sink,P];latest={}
@Sink
def sink(ctx,e,data,size):latest.update(epoch=e,serial=struct.unpack_from('<I',C.string_at(data,20),16)[0]);return 1
d.nf_live_completed_draw_scene_packet.argtypes=[C.c_uint64,U,P,P,P,U,P];d.nf_scene_packet_free.argtypes=[P]
def read(e,s):
 out=P();n=Z();poses=C.create_string_buffer(144*56);count=U();assert d.nf_live_completed_draw_scene_packet(e,s,C.byref(out),C.byref(n),poses,144,C.byref(count));return out,n.value,C.string_at(out,n.value),poses.raw[:count.value*56]
def reject(e,s):
 out=P(123);n=Z(999);poses=C.create_string_buffer(b'x'*8064);count=U(888);assert not d.nf_live_completed_draw_scene_packet(e,s,C.byref(out),C.byref(n),poses,144,C.byref(count));assert out.value==123 and n.value==999 and count.value==888 and poses.raw[:8064]==b'x'*8064
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0);assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
raw=rom.read_bytes();assert d.nf_live_visibility_enable(raw,len(raw),16*1024*1024);d.nf_live_surface_audit_enable(1);assert d.nf_layer_queue_enable(1)
run=p/'prototype-runs'/('exact-cache-'+uuid.uuid4().hex);inputs=[]
try:
 for i in range(120):keys=16 if 90<=i<92 else 0;inputs.append(keys);d.nf_frame(keys)
 e,s=latest['epoch'],latest['serial'];a,n,expected,cameras=read(e,s);b,m,second,second_cameras=read(e,s);assert a.value!=b.value and expected==second and cameras==second_cameras
 C.memset(a,165,n);d.nf_scene_packet_free(a);c,z,third,third_cameras=read(e,s);assert third==expected and third_cameras==cameras;d.nf_scene_packet_free(c)
 stats=(U*4)();d.nf_live_exact_scene_cache_stats(stats);assert stats[0]>=2 and stats[1]>=1 and stats[3]==0
 reject(e+1,s);reject(e,s+1000)
 for i in range(120,240):keys=16 if 180<=i<182 else 0;inputs.append(keys);d.nf_frame(keys)
 assert latest['serial']>=s+16;reject(e,s);assert C.string_at(b,m)==expected;d.nf_scene_packet_free(b)
 actual=[]
 for name,base,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  f=Path(str(run)+'-'+name+'.bin');d.nf_dump(str(f).encode(),base,size);actual.append(f.read_bytes())
 current=dict(latest);held,size,held_bytes,held_cameras=read(current['epoch'],current['serial']);d.nf_native_scene_discontinuity();reject(current['epoch'],current['serial']);assert C.string_at(held,size)==held_bytes;d.nf_scene_packet_free(held)
finally:d.nf_close()
b=C.CDLL(str(p.parent/'nfsprobe.dll'));b.nf_init.argtypes=[C.c_char_p]*2;b.nf_state.argtypes=[C.c_char_p,C.c_int];b.nf_dump.argtypes=[C.c_char_p,U,U];assert b.nf_init(str(rom).encode(),b'') and b.nf_state(str(state).encode(),0)
try:
 for keys in inputs:b.nf_frame(keys)
 for expected,(name,base,size) in zip(actual,[('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]):
  f=Path(str(run)+'-baseline-'+name+'.bin');b.nf_dump(str(f).encode(),base,size);assert f.read_bytes()==expected
finally:b.nf_close()
r=dict(result='PASS',original_updates=len(inputs),exact_original_ram=True,returned_buffer_mutation_independent=True,expired_serial_atomic_rejection=True,epoch_cut_atomic_rejection=True,owned_buffers_survive_expiry_and_cut=True,scope='Completed native scene cache ownership only; no fullscene60fps or physical controller claim.')
(p/'exact-scene-cache-tests.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
