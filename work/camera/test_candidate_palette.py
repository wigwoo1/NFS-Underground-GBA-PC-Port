from pathlib import Path
import ctypes as C,json
p=Path('work/camera');d=C.CDLL(str((p/'native_surface.dll').resolve()));d.nf_candidate_palette.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_uint,C.c_void_p]
checks=0
for index in range(256):
 indices=bytes([index]);palettes=bytearray(1024);palettes[512+index*2]=1;out=C.create_string_buffer(b'X'*512);before=out.raw
 assert not d.nf_candidate_palette(indices,1,bytes(palettes),2,out) and out.raw==before;checks+=1
 palettes[512+index*2]=0;palettes[512+((index+1)%256)*2]=1
 assert d.nf_candidate_palette(indices,1,bytes(palettes),2,out) and out.raw[:512]==bytes(512);checks+=1
for pixels,count in [(0,2),(1,0),(1,257),(1024*1024+1,2)]:
 out=C.create_string_buffer(b'X'*512);before=out.raw
 assert not d.nf_candidate_palette(b'\x00',pixels,bytes(1024),count,out) and out.raw==before;checks+=1
report=dict(result='PASS',checks=checks,scope='All256used indices reject conflicts atomically; unused changes allowed; size/count bounds fail closed. Unlit only.')
(p/'candidate-palette-tests.json').write_text(json.dumps(report,indent=2));print(report)
