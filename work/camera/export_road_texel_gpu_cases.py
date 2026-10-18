from pathlib import Path
import ctypes as C,struct,json,math
p=Path('work/camera');fn=C.CDLL(str((p/'road-pair-uv-continuous.dll').resolve())).nf_road_pair_uv_continuous;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_double,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());data=(p/'road-pair-uv-gpu-cases.bin').read_bytes();n=struct.unpack_from('<I',data)[0];records=[];fractions=[]
for i in range(n):
 r=list(struct.unpack_from('<10i',data,4+i*40));f=[((i*13+k*7)%16)/16 for k in range(8)]
 if r[7]==r[3]-1:f[7]=f[6]/2
 out=(C.c_double*2)();assert fn((C.c_double*3)(*(r[k]+f[k] for k in range(3))),(C.c_double*3)(*(r[4+k]+f[3+k] for k in range(3))),r[3]+f[6],r[7]+f[7],table,out);r[8:]=[(2*math.floor(out[0]/65536)+(i%2))%256,math.floor(out[1]/32768)%128];records.append(struct.pack('<10i',*r));fractions.append(struct.pack('<8f',*f))
(p/'road-pair-uv-texel-gpu-cases.bin').write_bytes(struct.pack('<I',n)+b''.join(records)+b''.join(fractions));print('fractional_cases',n)
