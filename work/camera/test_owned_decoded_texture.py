from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_decoded_texture_stats.argtypes=[C.c_void_p]
original=(p/'motion-actual-scanline-assets/8766-native-complete-frame.bin').read_bytes();offset=40;palette_offset=None;gn=struct.unpack_from('<I',original,8)[0]
while offset<40+gn:
 kind=struct.unpack_from('<I',original,offset+4)[0];offset+=16
 for i in range(12):
  n=struct.unpack_from('<I',original,offset)[0];offset+=4
  if kind==3 and i==11:palette_offset=offset
  offset+=n
assert palette_offset is not None;stats=(C.c_uint64*3)();rgb=C.create_string_buffer(3840*2160*3)
try:
 assert d.nf_owned_gpu_draw(original,len(original))==0;assert d.nf_owned_gpu_draw(original,len(original))==0
 d.nf_owned_decoded_texture_stats(stats);assert stats[0]>0;misses=stats[1]
 changed=bytearray(original);changed[palette_offset:palette_offset+512]=struct.pack('<H',31)*256
 frame=C.create_string_buffer(bytes(changed),len(changed));assert d.nf_owned_gpu_draw(frame,len(frame))==0;d.nf_owned_decoded_texture_stats(stats);assert stats[1]>misses
 assert d.nf_owned_gpu_read(rgb,len(rgb))==0;reference=(p/'owned-timed-8766.ppm').read_bytes().split(b'\n',3)[3];assert rgb.raw!=reference
 for color in range(35):
  changed[palette_offset:palette_offset+512]=struct.pack('<H',color)*256;frame=C.create_string_buffer(bytes(changed),len(changed));assert d.nf_owned_gpu_draw(frame,len(frame))==0
  d.nf_owned_decoded_texture_stats(stats);assert stats[2]<=16*1024*1024
 assert d.nf_owned_gpu_draw(original,len(original))==0;assert d.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==reference
 result=dict(result='PASS_EXACT_SOURCE_TEXTURE_EXPANSION_CACHE',hits=int(stats[0]),misses=int(stats[1]),retained_payload_bytes=int(stats[2]),palette_change_invalidates=True,bounded_eviction_and_original_restore=True)
finally:assert d.nf_owned_gpu_close()
d.nf_owned_decoded_texture_stats(stats);assert stats[2]==0;result['close_releases_cpu_payload']=True;(p/'owned-decoded-texture-tests.json').write_text(json.dumps(result,indent=2));print(result)
