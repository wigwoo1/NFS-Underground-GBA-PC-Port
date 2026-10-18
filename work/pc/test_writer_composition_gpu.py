from pathlib import Path
import ctypes as C,json,hashlib,os
import numpy as np
from PIL import Image
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-writer-composition-tests'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;D=C.c_double
class Draw(C.Structure):_fields_=[('owner',U),('count',U),('endpoint',U),('reserved',U),('bounds',U*4),('ring',D*36),('writer',P),('map',P)]
assert C.sizeof(Draw)==336
refsource=here/'test_recipe_writer.py';refprefix=refsource.read_text().split('writer_cases=cells=')[0];ref={'__file__':str(refsource),'__name__':'composition_original_recipe_inputs'};exec(compile(refprefix,str(refsource),'exec'),ref)
with os.add_dll_directory('C:/msys64/mingw64/bin'):regions=C.CDLL(str(out/'recipe-regions.dll'));baseline=C.CDLL(str(base/'NFSUG-pc-writer-band-tests/recipe-gpu.dll'))
def bind(lib,name,args,res=C.c_int):f=getattr(lib,name);f.argtypes=args;f.restype=res;return f
rc=bind(regions,'nf_pc_recipe_regions_create',[P,S],P);rb=bind(regions,'nf_pc_recipe_regions_buffer',[P,P,P]);rfree=bind(regions,'nf_pc_recipe_regions_free',[P],None)
prepared=[];handles=[];source_cells=0;retained_bytes=0;cap={}
def blob(f,*args):p=P();n=S();assert f(*args,C.byref(p),C.byref(n));return C.string_at(p,n.value)
def capture_scene(frame,scene,meta):
 global source_cells,retained_bytes
 if meta[1] not in [12434,12437,12438]:return
 d=cap['d'];coverage=bind(d,'nf_pc_source_recipe_coverage',[P,U,U,S],P);cf=bind(d,'nf_pc_recipe_coverage_free',[P],None);cb=bind(d,'nf_pc_recipe_coverage_buffer',[P,U,P,P]);op=bind(d,'nf_pc_recipe_writer_decode',[P,U,Q,U,P,U,S],P);am=bind(d,'nf_pc_writer_address_map',[P,S],P);sample=bind(d,'nf_pc_recipe_writer_cell',[P,U,U,P]);wi=bind(d,'nf_pc_recipe_writer_info',[P,P]);mi=bind(d,'nf_pc_writer_address_map_info',[P,P]);packets=[];keys=[];cache={}
 for kind in [2,3]:
  for owner in range(meta[4]):
   key=(Q*5)();assert cap['oi'](frame,owner,key);keys.append(list(key));cov=coverage(frame,owner,kind,64*1024*1024);assert cov
   try:
    records=np.frombuffer(blob(cb,cov,2),'<u8').reshape(-1,6).copy();r=rc(cov,64*1024*1024);assert r
    try:rects=np.frombuffer(blob(rb,r),'<u8').reshape(-1,8).copy()
    finally:rfree(r)
    for row in records:
     cell,epoch,rkind,ordinal,write,index=map(int,row);lookup=(owner,rkind,ordinal)
     if lookup not in cache:
      values,archive_write=ref['recipes'][(rkind,ordinal)];assert archive_write==write;keep,blocks=ref['make'](values);w=op(key,rkind,ordinal,write,blocks,15,64*1024*1024);assert w;m=am(w,64*1024*1024);assert m;cache[lookup]=(w,m);handles.append((w,m));info=(Q*10)();info_map=(Q*15)();assert wi(w,info) and mi(m,info_map);retained_bytes+=info[9]+info_map[14]
     value=(Q*4)();assert sample(cache[lookup][0],cell%240,cell//240,value) and value[3] and value[2]==index;source_cells+=1
    for epoch,rkind,ordinal,write,left,right,top,bottom in rects:
     left,right,top,bottom=map(int,[left,right,top,bottom]);w,m=cache[(owner,int(rkind),int(ordinal))];ring=(D*36)(left,top,128,left,top,1,right,top,128,right,top,1,right,bottom,128,right,bottom,1,left,bottom,128,left,bottom,1);packets.append(Draw(owner,4,1,0,(U*4)(left,right,top,bottom),ring,w,m))
   finally:cf(cov)
 prepared.append(dict(scene=scene,refresh=int(meta[1]),owners=int(meta[4]),split=int(meta[3]),packets=(Draw*len(packets))(*packets),packet_count=len(packets),writer_bindings=len(cache),owner_keys=keys));print('PREPARED_COMPLETE_SOURCE_WRITER_SCENE',meta[1],len(packets),'regions',len(cache),'writers',flush=True)
original=here/'test_writer_scene_gpu.py';prefix=original.read_text().split("original=here/'test_writer_gpu.py'")[0].replace('NFSUG-pc-writer-scene-tests','NFSUG-pc-writer-composition-tests');anchor='assert scene;scenes.append(scene)';assert prefix.count(anchor)==1;prefix=prefix.replace(anchor,anchor+';capture_scene(f,scene,meta)');cap.update(__file__=str(original),__name__='composition_capture',capture_scene=capture_scene)
try:
 exec(compile(prefix,str(original),'exec'),cap)
 assert len(prepared)==3
 d=cap['d'];open_gpu=bind(d,'nf_pc_scene_gpu_open',[],P);close_gpu=bind(d,'nf_pc_scene_gpu_close',[P],None);draw=bind(d,'nf_pc_scene_gpu_draw_source_writers',[P,P,U,U,U,U,P,S,P,S]);oldopen=bind(baseline,'nf_pc_scene_gpu_open',[],P);oldclose=bind(baseline,'nf_pc_scene_gpu_close',[P],None);old=bind(baseline,'nf_pc_scene_gpu_draw',[P,P,U,U,U,U,P,S]);canonical_draw=bind(d,'nf_pc_scene_gpu_draw_integer_retention_reference',[P,P,U,U,U,U,P,S]);render_only=bind(d,'nf_pc_scene_gpu_render_source_writers',[P,P,U,U,U,U,P,S]);normal=bind(d,'nf_pc_scene_gpu_draw',[P,P,U,U,U,U,P,S]);read=bind(d,'nf_pc_scene_gpu_read_target',[P,P,S]);g=open_gpu();og=oldopen();assert g and og;rows=[];images={};guard_count=0
 try:
  for item in prepared:
   scene=item['scene'];packets=item['packets'];count=item['packet_count']
   for width,height,aw,ah in [(240,160,240,160),(3840,2160,3240,2160)]:
    size=width*height*4;want=C.create_string_buffer(size);actual=C.create_string_buffer(size);after=C.create_string_buffer(size);assert old(og,scene,width,height,aw,ah,want,size)
    canonical=C.create_string_buffer(size);assert canonical_draw(g,scene,width,height,aw,ah,canonical,size)
    assert draw(g,scene,width,height,aw,ah,packets,count,actual,size),bind(d,'nf_pc_scene_gpu_error',[],C.c_char_p)();a=np.frombuffer(actual.raw,np.uint8).reshape(height,width,4);legacy=np.frombuffer(want.raw,np.uint8).reshape(height,width,4);b=np.frombuffer(canonical.raw,np.uint8).reshape(height,width,4);diff=np.any(a!=b,axis=2);legacy_diff=np.any(a!=legacy,axis=2);ly,lx=np.nonzero(legacy_diff);source_x=(lx+.5)*240/aw;source_y=(ah-ly-.5)*160/ah;on_grid=(np.abs(source_x-np.rint(source_x))<1e-8)|(np.abs(source_y-np.rint(source_y))<1e-8);assert on_grid.all(),('Legacy differences away from exact integer cell boundaries',item['refresh'],width);assert width!=240 or not legacy_diff.any()
    if diff.any():Image.fromarray(a[::-1]).save(out/'composition-failure-actual.png');Image.fromarray(b[::-1]).save(out/'composition-failure-expected.png')
    assert not diff.any(),('Complete scene source writer differs',item['refresh'],width,int(diff.sum()),np.argwhere(diff)[:10].tolist())
    assert render_only(g,scene,width,height,aw,ah,packets,count) and read(g,after,size) and after.raw==canonical.raw
    # Ordinary rendering after the route must restore normal path, not leave a borrowed list installed.
    assert normal(g,scene,width,height,aw,ah,after,size) and after.raw==want.raw
    first=packets[0];saved=first.reserved;first.reserved=1;assert not draw(g,scene,width,height,aw,ah,packets,count,actual,size);assert read(g,actual,size) and actual.raw==want.raw;first.reserved=saved;guard_count+=1
    saved=first.owner;first.owner=99;assert not draw(g,scene,width,height,aw,ah,packets,count,actual,size);assert read(g,actual,size) and actual.raw==want.raw;first.owner=saved;guard_count+=1
    assert not draw(g,scene,width,height,aw,ah,None,count,actual,size);assert read(g,actual,size) and actual.raw==want.raw;guard_count+=1
    rows.append(dict(refresh=item['refresh'],size=[width,height,aw,ah],packet_count=count,writer_bindings=item['writer_bindings'],owners=item['owners'],split_row=item['split'],pixel_differences=0,legacy_exact_grid_edge_differences=int(legacy_diff.sum()),legacy_off_grid_differences=0))
    if width==3840:
     path=out/('complete-source-writers-'+str(item['refresh'])+'-4k.png');Image.fromarray(a[::-1]).save(path);images[path.name]=sha(path);legacy_path=out/('legacy-complete-'+str(item['refresh'])+'-4k.png');Image.fromarray(legacy[::-1]).save(legacy_path);images[legacy_path.name]=sha(legacy_path)
    print('COMPLETE_SCENE_SOURCE_WRITER_PASS',item['refresh'],width,flush=True)
 finally:close_gpu(g);oldclose(og)
finally:
 if 'd' in cap:
  for w,m in handles:bind(cap['d'],'nf_pc_writer_address_map_free',[P],None)(m);bind(cap['d'],'nf_pc_recipe_writer_free',[P],None)(w)
  for scene in cap.get('scenes',[]):cap['sf'](scene)
r=dict(result='PASS_COMPLETE_SCENE_RAW_SOURCE_WRITERS_INTEGER_REFERENCE',cases=len(rows),rows=rows,pixel_differences=0,source_cells_independently_checked=source_cells,owned_writer_bindings=len(handles),writer_and_address_retained_bytes=retained_bytes,invalid_lists_rejected_without_target_changes=guard_count,scene_frame_reader_core_closed_before_render=True,normal_render_after_new_route_exact=True,original_replay_frames_exact=600,audio_frames=cap['samples'],audio_sha256=cap['digest'].hexdigest(),rom_state_unchanged=cap['unchanged'],diagnostic_images=images,gpu_dll_sha256=sha(out/'recipe-gpu.dll'),baseline_gpu_sha256=sha(base/'NFSUG-pc-writer-band-tests/recipe-gpu.dll'),script_sha256=sha(Path(__file__)),capture_source_sha256=sha(original),capture_executed_prefix_sha256=hashlib.sha256(prefix.encode()).hexdigest(),original_writer_source_sha256=sha(refsource),original_writer_executed_prefix_sha256=hashlib.sha256(refprefix.encode()).hexdigest(),full_scene_60fps=False,live_integration=False,legacy_grid_edge_differences=sum(row['legacy_exact_grid_edge_differences'] for row in rows),legacy_off_grid_differences=0,integer_retention_reference_exact=True,render_without_cpu_readback_exact=True,scope='Complete captured endpoint scenes strictly equal independent integer retention reference; legacy cell-quad raster differs only at exact source-cell grid edges.  raw writer textures replace retained color/index atlases while background, ordered main geometry and HUD remain original endpoint. No complete-scene fractional motion/visibility or performance claim.')
(out/'writer-composition-test-report.json').write_text(json.dumps(r,indent=2));print({k:v for k,v in r.items() if k not in ['rows','diagnostic_images']})
