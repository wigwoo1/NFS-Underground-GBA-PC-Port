from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');fn=C.CDLL(str((p/'road-pair-uv-continuous.dll').resolve())).nf_road_pair_uv_continuous;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_double,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());data=(p/'road-pair-uv-gpu-cases.bin').read_bytes();n=struct.unpack_from('<I',data)[0];records=[]
for i in range(n):
 r=list(struct.unpack_from('<10i',data,4+i*40));out=(C.c_double*2)();assert fn((C.c_double*3)(*(v+.25 for v in r[:3])),(C.c_double*3)(*(v+.25 for v in r[4:7])),r[3]+.5,r[7]+.25,table,out);r[8:]=[round(v) for v in out];records.append(struct.pack('<10i',*r))
(p/'road-pair-uv-fractional-gpu-cases.bin').write_bytes(struct.pack('<I',n)+b''.join(records));print('fractional_cases',n)
