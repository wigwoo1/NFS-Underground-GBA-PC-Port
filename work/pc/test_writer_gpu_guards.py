from pathlib import Path
import ctypes as C,json,hashlib,threading
here=Path(__file__).resolve().parent;original=here/'test_writer_gpu_synthetic.py';boot=original.read_text().split('try:\n for name,kind,command,texture,shade in cases:')[0];ns={'__file__':str(original),'__name__':'writer_guard_inputs'};exec(compile(boot,str(original),'exec'),ns)
P=ns['P'];S=ns['S'];U=ns['U'];Q=ns['Q'];g=ns['g'];out=ns['out'];fn=ns['fn'];ref=ns['ref'];draw=ns['draw'];read=ns['read'];ring=ns['ring'];bounds=ns['bounds'];pb=ns['pb'];w1=w2=m1=m2=None;guards=0

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
ab=fn('nf_pc_writer_address_map_buffer',[P,P,P]);ai=ns['ai']
def contents(m):p=P();n=S();assert ab(m,C.byref(p),C.byref(n));return C.string_at(p,n.value)
try:
 _,kind,command,texture,shade=ns['cases'][0];keep1,blocks=ref['fixture'](kind,command,texture,shade);w1=ns['op'](ref['owner'],kind,ref['ordinal'],8,blocks,15,64*1024*1024);assert w1;m1=ns['amap'](w1,64*1024*1024);assert m1
 _,kind,command,texture,shade=ns['cases'][2];keep2,blocks=ref['fixture'](kind,command,texture,shade);w2=ns['op'](ref['owner'],kind,ref['ordinal'],8,blocks,15,64*1024*1024);assert w2;m2=ns['amap'](w2,64*1024*1024);assert m2
 assert not draw(g,ring,4,bounds,w1,m1,pb,len(pb),240,160,1,0);guards+=1
 pixels=C.create_string_buffer(153600);assert ns['seed'](g,ns['zero'],15136,ns['zero'],15136,0,ns['empty'],163840,240,160,240,160,0,0,pixels,len(pixels));assert draw(g,ring,4,bounds,w1,m1,pb,len(pb),240,160,1,0);assert read(g,pixels,len(pixels));snapshot=pixels.raw
 for writer,map in [(None,m1),(w1,None),(w1,m2),(w2,m1)]:
  assert not draw(g,ring,4,bounds,writer,map,pb,len(pb),240,160,1,0);assert read(g,pixels,len(pixels)) and pixels.raw==snapshot;guards+=1
 results=[]
 def worker():results.append(draw(g,ring,4,bounds,w1,m1,pb,len(pb),240,160,1,0))
 t=threading.Thread(target=worker);t.start();t.join();assert results==[0] and read(g,pixels,len(pixels)) and pixels.raw==snapshot;guards+=1
 for v in keep1:C.memset(v,0,len(v))
 assert draw(g,ring,4,bounds,w1,m1,pb,len(pb),240,160,1,0) and read(g,pixels,len(pixels)) and pixels.raw==snapshot
 owned=contents(m1);ns['wf'](w1);w1=None;assert contents(m1)==owned
finally:
 for m in [m1,m2]:
  if m:ns['af'](m)
 for w in [w1,w2]:
  if w:ns['wf'](w)
 ns['close'](g)
r=dict(result='PASS_WRITER_GPU_KEY_THREAD_AND_OWNERSHIP_GUARDS',requests_rejected_without_target_changes=guards,address_map_survives_writer_free=True,gpu_upload_survives_input_buffer_overwrite=True,gpu_dll_sha256=sha(out/'recipe-gpu.dll'),build_report_sha256=sha(out/'recipe-gpu-build-report.json'),source_fixture_test_sha256=sha(original),executed_prefix_sha256=hashlib.sha256(boot.encode()).hexdigest(),script_sha256=sha(Path(__file__)),full_scene_60fps=False);(out/'writer-gpu-guard-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
