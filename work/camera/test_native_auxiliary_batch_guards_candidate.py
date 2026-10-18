import ctypes as C,json,threading
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'owned-d3d-auxiliary-batch-candidate.dll').resolve()));P=C.c_void_p;Info=C.CFUNCTYPE(C.c_int,P,P);HUDInfo=C.CFUNCTYPE(C.c_int,P);Copy=C.CFUNCTYPE(C.c_int,C.c_uint,P,C.c_size_t);Count=C.CFUNCTYPE(C.c_uint);Records=C.CFUNCTYPE(C.c_int,P,C.c_size_t)
d.nf_d3d_source_sky_batch.argtypes=[P,P];d.nf_d3d_source_hud_batch.argtypes=[P,P,P,P];assert d.nf_d3d_open()==0;calls=[]
@Info
def disabled(v,a):calls.append('sky_info');C.cast(v,C.POINTER(C.c_uint))[0]=0;C.cast(v,C.POINTER(C.c_uint))[1]=0;return 0
@Info
def invalid(v,a):C.cast(v,C.POINTER(C.c_uint))[0]=2;C.cast(v,C.POINTER(C.c_uint))[1]=0;return 0
@Copy
def copy(*args):calls.append('copy');return 1
@HUDInfo
def hud(v):C.cast(v,C.POINTER(C.c_uint))[0]=1;return 0
@Count
def count():return 161
@Records
def records(*args):calls.append('records');return 1
try:
 assert d.nf_d3d_source_sky_batch(disabled,copy)==0;assert calls==['sky_info'];assert d.nf_d3d_source_sky_batch(invalid,copy)==1;assert calls==['sky_info']
 assert d.nf_d3d_source_hud_batch(hud,copy,count,records)==1;assert calls==['sky_info']
 assert d.nf_d3d_source_sky_batch(None,copy)==1
 wrong=[];t=threading.Thread(target=lambda:wrong.append(d.nf_d3d_source_sky_batch(disabled,copy)));t.start();t.join();assert wrong==[1] and calls==['sky_info']
finally:assert d.nf_d3d_close()==0
out=dict(result='PASS_AUXILIARY_BATCH_DISABLED_INVALID_CAPACITY_OWNER',scope='Synthetic source metadata guards; actual source-plane pixel parity verified separately.')
(p/'prototype-runs/native-auxiliary-batch-guards-20261008.json').write_text(json.dumps(out,indent=2));print(out['result'])
