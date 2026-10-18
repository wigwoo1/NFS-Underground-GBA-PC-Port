"""Private loaded-state DMA positive control; never saves mutated state."""
from pathlib import Path
import ctypes as C,json
p=Path(__file__).resolve().parent
exec(compile((p/'test_live_owned_indexed_copy.py').read_text().split("\nassert d.nf_init(session['rom'].encode(),b'')")[0],str(p/'test_live_owned_indexed_copy.py'),'exec'))
d.nf_write.argtypes=[U,U,C.c_int];d.nf_page_write_audit_enable.argtypes=[U];d.nf_page_write_audit_origins_copy.argtypes=[P];d.nf_page_write_audit_generation_copy.argtypes=[P];checks=[]
for page in [0,1]:
 assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
 try:
  for i in range(4):d.nf_write(0x0203f000+i*4,0x12345678+i,4)
  d.nf_page_write_audit_generation_reset();d.nf_page_write_audit_enable(1)
  d.nf_write(0x040000d4,0x0203f000,4);d.nf_write(0x040000d8,0x06000000+page*0xa000,4);d.nf_write(0x040000dc,0x84000004,4);d.nf_frame(0)
  counts=(C.c_uint64*4)();assert d.nf_page_write_audit_origins_copy(counts);assert list(counts[2:])==([16,0] if page==0 else [0,16]),list(counts)
  generation=(C.c_uint64*2)();assert d.nf_page_write_audit_generation_copy(generation);assert list(generation)==[counts[i]+counts[i+2] for i in range(2)]
  prior=list(generation);d.nf_page_write_audit_enable(1);assert d.nf_page_write_audit_generation_copy(generation) and list(generation)==prior
  d.nf_page_write_audit_generation_reset();assert d.nf_page_write_audit_generation_copy(generation) and list(generation)==[0,0]
  checks.append(dict(page=page,cpu_bytes=list(counts[:2]),dma_bytes=list(counts[2:]),generation_before_reset=prior,per_update_reset_preserves_generation=True,explicit_generation_reset=True))
 finally:d.nf_close()
r=dict(result='PASS',checks=checks,scope='Actual immediate DMA3 service callback positive control in private unsaved state; original ledger verification separate');(p/'page-dma-observer-test.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
