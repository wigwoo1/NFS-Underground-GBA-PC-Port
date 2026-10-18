from pathlib import Path
import ctypes as C,json,hashlib,struct
import numpy as np
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-writer-band-tests'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
original=here/'test_writer_gpu_synthetic.py';boot=original.read_text().split('try:\n for name,kind,command,texture,shade in cases:')[0].replace('NFSUG-pc-writer-gpu-tests','NFSUG-pc-writer-band-tests');ns={'__file__':str(original),'__name__':'band_fixture_inputs'};exec(compile(boot,str(original),'exec'),ns)
P,S,U,Q,D=[ns[k] for k in ['P','S','U','Q','D']];fn=ns['fn'];g=ns['g'];draw=ns['draw'];read=ns['read'];seed=ns['seed'];ref=ns['ref'];pb=ns['pb'];bounds=ns['bounds'];band=fn('nf_pc_scene_gpu_render_writer_band',[P,P,U,P,P,P,P,S,U,U,U,U,U,U]);w=m=None;rows=[];guards=0;pixels_checked=0;covered_checked=0
try:
 command=[0]*20;command[2]=120;command[4]=1;command[9]=0x08000000;command[17]=0x06000000+120;command[19]=160
 keep,blocks=ref['fixture'](2,command,bytes([17])*65536,b'\0');w=ns['op'](ref['owner'],2,ref['ordinal'],8,blocks,15,64*1024*1024);assert w;m=ns['amap'](w,64*1024*1024);assert m
 for width,height,aw,ah in [(240,160,240,160),(241,161,241,161),(3840,2160,3240,2160)]:
  splits=range(161) if width!=3840 else [0,1,49,50,77,78,80,159,160]
  for shift in [0.,-23.5,23.5]:
   ring=(D*24)(0,shift,128,0,0,1,240,shift,128,240,0,1,240,160+shift,128,240,160,1,0,160+shift,128,0,160,1);endpoint=int(shift==0)
   size=width*height*4;buf=C.create_string_buffer(size)
   def clear():assert seed(g,ns['zero'],15136,ns['zero'],15136,0,ns['empty'],163840,width,height,aw,ah,0,0,buf,size)
   def get():assert read(g,buf,size);return np.frombuffer(buf.raw,np.uint8).reshape(height,width,4).copy()
   clear();assert draw(g,ring,4,bounds,w,m,pb,163840,aw,ah,endpoint,0);full=get();display_rows=(((ah-np.arange(ah,dtype=np.int64))*2-1)*80)//ah
   assert np.count_nonzero(full[:,:,3])>0
   for split in splits:
    for top,bottom in [(0,split),(split,160)]:
     clear();assert band(g,ring,4,bounds,w,m,pb,163840,aw,ah,endpoint,0,top,bottom);actual=get();expected=full.copy();outside=(display_rows<top)|(display_rows>=bottom);expected[np.nonzero(outside)[0],:aw]=0
     assert np.array_equal(actual,expected),('Band mismatch',width,shift,top,bottom,int(np.any(actual!=expected,axis=2).sum()));pixels_checked+=width*height;covered_checked+=int(np.count_nonzero(actual[:,:,3]))
    # Complement bands must reconstruct full coverage in either submission order.
    for order in [[(0,split),(split,160)],[(split,160),(0,split)]]:
     clear()
     for top,bottom in order:assert band(g,ring,4,bounds,w,m,pb,163840,aw,ah,endpoint,0,top,bottom)
     assert np.array_equal(get(),full),('Complement gap/overlap',width,shift,split,order);pixels_checked+=width*height
    rows.append(dict(size=[width,height,aw,ah],shift=shift,split=split))
   snapshot=buf.raw
   for top,bottom in [(1,0),(0,161),(161,161),(0,2**32-1)]:
    assert not band(g,ring,4,bounds,w,m,pb,163840,aw,ah,endpoint,0,top,bottom);assert read(g,buf,size) and buf.raw==snapshot;guards+=1
   print('BAND_PASS',width,shift,len(splits),'splits',flush=True)
finally:
 if m:ns['af'](m)
 if w:ns['wf'](w)
 ns['close'](g)
r=dict(result='PASS_EXACT_DESTINATION_OWNER_BAND_PARTITION',cases=len(rows),pixels_checked=pixels_checked,covered_band_pixels_checked=covered_checked,invalid_band_requests=guards,pixel_differences=0,all_161_native_split_rows=True,odd_active_dimensions=True,complement_bands_reconstruct_in_both_orders=True,endpoint_and_fractional_translations=True,gpu_dll_sha256=sha(out/'recipe-gpu.dll'),script_sha256=sha(Path(__file__)),input_source_sha256=sha(original),executed_prefix_sha256=hashlib.sha256(boot.encode()).hexdigest(),rows=rows,full_scene_60fps=False,scope='Dense original wall command; exact differential integer destination-row clipping and complement partition. Not scene visibility/new geometry policy.')
(out/'writer-band-test-report.json').write_text(json.dumps(r,indent=2));print({k:v for k,v in r.items() if k!='rows'})
