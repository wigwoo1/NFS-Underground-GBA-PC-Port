import ctypes as C,json
from pathlib import Path
p=Path('work/camera');s=C.CDLL(str((p/'owned-gpu-source-sealed-fault-candidate.dll').resolve()));s.nf_source_packets_begin.argtypes=[C.c_uint64]*3;s.nf_source_packets_publish.argtypes=[C.c_void_p];checks=[]
for mode in range(1,6):
 assert s.nf_source_packets_begin(1,1,mode)==0;assert s.nf_source_test_incomplete(mode)==0
 out=(C.c_uint64*7)(*[999]*7);assert s.nf_source_packets_publish(out)==1 and list(out)==[999]*7
 assert s.nf_source_packets_close()==0;assert s.nf_source_packets_begin(1,2,mode)==0;assert s.nf_source_packets_publish(out)==0;assert s.nf_source_test_incomplete(mode)==1;assert s.nf_source_packets_close()==0
 checks.append(dict(fault=mode,incomplete_rejected=True,output_unchanged=True,new_generation_recovers=True,frozen_mutation_rejected=True))
r=dict(result='PASS_SOURCE_PUBLICATION_COMPLETENESS_FAULTS',checks=checks,scope='Test-only fault export excluded from normal DLL; partial backdrop, absent HUD batches/planes, row gap and upper-sky without lower rejected.');(p/'prototype-runs/source-sealed-fault-component.json').write_text(json.dumps(r,indent=2));print(r)
