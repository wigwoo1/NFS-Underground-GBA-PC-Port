"""Read-only original call trace during repeated hidden-page render passes."""
from pathlib import Path
import ctypes as C,csv,json,hashlib,sys
p=Path(__file__).resolve().parent
exec(compile((p/'diagnose_late_model_pairs.py').read_text().split("assert d.nf_init(session['rom'].encode(),b'')")[0],str(p/'diagnose_late_model_pairs.py'),'exec'))
prefix=p/'prototype-runs/threaded-prepared-4c0a478bbea14eedbc3a639513b0b9d6'
session=json.loads(Path(str(prefix)+'-session.json').read_text())
for name in ['rom','state']:assert hashlib.sha256(Path(session[name]).read_bytes()).hexdigest()==session[name+'_sha256'].lower()
d.nf_calls.argtypes=[C.c_char_p]
d.nf_image_copy_trace.argtypes=[C.c_char_p]
assert crt._putenv_s(b'NF_TRACE_INDIRECT_CALLS',b'1')==0
begin=int(sys.argv[1]) if len(sys.argv)>1 else 3523
end=int(sys.argv[2]) if len(sys.argv)>2 else 3534
assert 3400<=begin<end<=3700 and end-begin<=32
label='hidden-page' if begin==3523 else f'hidden-page-{begin}'
trace=p/(label+'-calls.csv')
assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
d.nf_read.argtypes=[U,C.c_int];d.nf_read.restype=U
fill_code=b''.join(d.nf_read(0x030002c0+i,4).to_bytes(4,'little') for i in range(0,96,4))
try:
 assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
 rom=Path(session['rom']).read_bytes();assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024)
 assert d.nf_layer_queue_enable(1)
 active=False
 for row in csv.DictReader(Path(str(prefix)+'-input.csv').open()):
  current=d.nf_layer_queue_latest()
  if current==begin and not active:
   d.nf_calls(str(trace).encode());assert d.nf_image_copy_trace(str(p/(label+'-image-copies.csv')).encode());active=True
  if current==end and active:d.nf_calls(None);assert d.nf_image_copy_trace(None);break
  d.nf_frame(int(row['keys']))
finally:d.nf_calls(None);d.nf_image_copy_trace(None);d.nf_close()
assert active and trace.exists()
calls=list(csv.DictReader(trace.open()));assert calls
interesting=[];counts={}
for call in calls:
 target=int(call['target'],16);counts[target]=counts.get(target,0)+1
 registers=[int(call['r'+str(i)],16) for i in range(4)]
 if any(0x06000000<=x<0x06018000 for x in registers):interesting.append(call)
import sys
sys.path.insert(0,str(p.parent/'pydeps'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
disassembly=[dict(address=hex(i.address),instruction=i.mnemonic+' '+i.op_str) for i in Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(fill_code,0x030002c0)]
report=dict(result='AUDITED',trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),calls=len(calls),frame_range=[min(int(x['frame']) for x in calls),max(int(x['frame']) for x in calls)],framebuffer_argument_calls=interesting,target_counts={hex(k):v for k,v in sorted(counts.items())},fill_code_hex=fill_code.hex(),fill_disassembly=disassembly,scope='Original existing Thumb BL logger plus opt-in resolved compiler BX veneers; incomplete CPU/ARM/other indirect/DMA write coverage. Framebuffer-valued argument alone is not proof of a clear.')
(p/(label+'-call-audit.json')).write_text(json.dumps(report,indent=2))
print(json.dumps(dict(calls=len(calls),frame_range=report['frame_range'],framebuffer_argument_calls=interesting),indent=2))
