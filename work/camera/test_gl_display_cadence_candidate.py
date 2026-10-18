import ctypes as C,json,threading
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'owned-gpu-gl-display-cadence-candidate.dll').resolve()))
assert d.nf_owned_gpu_window(0)==0
assert d.nf_owned_gpu_cadence_probe()==0
foreign=[];t=threading.Thread(target=lambda:foreign.append(d.nf_owned_gpu_cadence_probe()));t.start();t.join();assert foreign==[31]
row=(C.c_uint64*22)();d.nf_owned_gpu_cadence_read.argtypes=[C.c_uint,C.c_void_p];assert d.nf_owned_gpu_cadence_read(0,row)==0 and row[3]<=row[4] and row[5]>0 and d.nf_owned_gpu_cadence_count()==1
assert d.nf_owned_gpu_close();assert d.nf_owned_gpu_cadence_probe()==31
out=dict(result='PASS_OWNER_CONTEXT_CADENCE_COMPONENT',row=list(row),foreign_thread_rejected=True,closed_context_rejected=True,scope='Read-only composition/capability evidence, not scanout proof.')
(p/'prototype-runs/gl-cadence-component.json').write_text(json.dumps(out,indent=2));print(out)
