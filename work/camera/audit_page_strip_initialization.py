"""Original saved-state strip provenance; CPU observer never resets in ledger."""
from pathlib import Path
from project_paths import load_session
import ctypes as C,csv,json,hashlib
p=Path(__file__).resolve().parent
exec(compile((p/'diagnose_late_model_pairs.py').read_text().split("assert d.nf_init(session['rom'].encode(),b'')")[0],str(p/'diagnose_late_model_pairs.py'),'exec'))
prefix=p/'prototype-runs/threaded-prepared-4c0a478bbea14eedbc3a639513b0b9d6'
session=load_session(Path(str(prefix)+'-session.json'));rom=Path(session['rom']).read_bytes()
d.nf_page_write_audit_enable.argtypes=[U];d.nf_page_write_audit_copy.argtypes=[P,U];d.nf_read.argtypes=[U,C.c_int];d.nf_read.restype=U
runs=[]
for observe in [False,True]:
 assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
 try:
  assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
  assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024)
  initial=bytes(d.nf_read(0x06000000+y*240+x,1)&255 for y in range(16,24) for x in range(240))
  d.nf_page_write_audit_enable(observe);samples=[]
  for row in csv.DictReader(Path(str(prefix)+'-input.csv').open()):
   d.nf_frame(int(row['keys']))
   if latest.get('serial') in [22,38] and not any(x['serial']==latest['serial'] for x in samples):
    strip=bytes(d.nf_read(0x06000000+y*240+x,1)&255 for y in range(16,24) for x in range(240))
    record=dict(serial=latest['serial'],indices=sorted(set(strip)),initial_exact=strip==initial)
    if observe:
     writers=(U*(240*160))();assert d.nf_page_write_audit_copy(writers,C.sizeof(writers))
     record['writers']=sorted(set(hex(x) for x in writers[16*240:24*240]));record['written_pixels']=sum(x!=0 for x in writers[16*240:24*240])
    samples.append(record)
  hashes={}
  for name,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
   path=p/('strip-audit-'+name+'.bin');d.nf_dump(str(path).encode(),address,size);raw=path.read_bytes();path.unlink();assert raw==Path(str(prefix)+'-'+name+'.bin').read_bytes();hashes[name]=hashlib.sha256(raw).hexdigest()
  runs.append(dict(observed=observe,initial_values=sorted(set(initial)),initial_strip_sha256=hashlib.sha256(initial).hexdigest(),samples=samples,ram=hashes))
 finally:d.nf_close()
assert runs[0]['ram']==runs[1]['ram']
report=dict(result='AUDITED',state_sha256=session['state_sha256'],rows=[16,24],pixels=1920,runs=runs,scope='Checkpoint strip plus cumulative CPU writes across278updates. DMA execution and pre-checkpoint initializer not proven; no3D framebuffer asset captured.')
(p/'page-strip-initialization-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
