"""Writer-labelled transported masks; deliberately no game-material claims."""
from pathlib import Path
import os,ctypes as C,json,struct,zlib,hashlib
import numpy as np
from PIL import Image
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-region-gpu-tests';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
original=here/'test_recipe_regions.py';prefix=original.read_text().split('region_cases=rectangles=')[0];env={'__file__':str(original),'__name__':'region_gpu_inputs'};exec(compile(prefix,str(original),'exec'),env)
archive=env['ns'];regionlib=env['d'];fn=env['fn'];P=env['P'];S=env['S'];Q=env['Q'];U=env['U'];D=env['D'];make=env['make'];blob=env['blob'];cover=env['cover'];cf=env['cf'];cbuffer=env['cbuffer'];create=env['create'];free=env['free'];rbuffer=env['buffer'];ring=env['ring'];gd=env['gd'];gf=env['gf'];fc=env['fc'];ff=env['ff'];mesh=env['mesh'];mf=env['mf'];A=env['A'];B=env['B'];CA=env['CA'];CB=env['CB'];projection=env['projection'];a=env['a'];b=env['b']
regionbuild=json.loads((base/'NFSUG-pc-recipe-region-tests/region-build-report.json').read_text());gpuout=base/'NFSUG-pc-recipe-gpu-tests';gb=json.loads((gpuout/'recipe-gpu-build-report.json').read_text());assert sha(gpuout/'recipe-gpu.dll')==gb['dll_sha256']
for name in ['recipe_mesh.c','recipe_mesh.h']:
 p=str(here/name);paths=[k for k in regionbuild['source_sha256'] if Path(k).name==name];other=[k for k in gb['source_sha256'] if Path(k).name==name];assert len(paths)==len(other)==1 and regionbuild['source_sha256'][paths[0]]==gb['source_sha256'][other[0]]==sha(here/name)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(gpuout/'recipe-gpu.dll'))
op=fn(d,'nf_pc_scene_gpu_open',[],P);close=fn(d,'nf_pc_scene_gpu_close',[P],None);error=fn(d,'nf_pc_scene_gpu_error',[],C.c_char_p);renderer=fn(d,'nf_pc_scene_gpu_renderer',[P],C.c_char_p);seed=fn(d,'nf_pc_scene_gpu_draw_sky',[P,P,S,P,S,D,P,S,U,U,U,U,U,U,P,S]);read=fn(d,'nf_pc_scene_gpu_read_target',[P,P,S]);submit=fn(d,'nf_pc_scene_gpu_render_recipe',[P,P,P,P,S,U,U,P]);mat=fn(d,'nf_pc_recipe_material_decode',[U,P,U,S],P);mtf=fn(d,'nf_pc_recipe_material_free',[P],None);vertices=fn(regionlib,'nf_pc_recipe_mesh_vertices',[P,P,P])
values=[b'\0']*15;mb=bytearray(48);mb[38:40]=b'\1\0';values[4]=bytes(mb);values[8]=bytes([1])*65536;keep,bs=make(values);material=mat(2,bs,15,65536);assert material
zero=bytes(15136);empty_palette=bytes(163840);gpu=op();assert gpu,error();gpu_name=renderer(gpu).decode();rows=[];compared=boundary=boundary_diff=full_endpoint_diff=native_endpoint_pixels=0;cr=json.loads((base/'NFSUG-pc-recipe-coverage-tests/coverage-test-report.json').read_text());image_hashes={}
def label(kind,ordinal):return np.array([ordinal&255,(ordinal>>8)&255,kind,255],np.uint8)
try:
 for name,h in cr['fixture_sha256'].items():
  path=base/'NFSUG-pc-recipe-coverage-tests'/name;assert sha(path)==h;raw=zlib.decompress(path.read_bytes()[8:]);fields=struct.unpack_from('<5Q4I',raw);key=(Q*5)(*fields[:5]);kind,top,bottom,hn=fields[5:];history=raw[56:56+hn];proof=raw[56+hn:];c=cover(history,len(history),proof,len(proof),key,kind,top,bottom,64*1024*1024);assert c;records=np.frombuffer(blob(cbuffer,c,2),'<u8').reshape(-1,6).copy();regions=create(c,64*1024*1024);assert regions;cf(c);rects=np.frombuffer(blob(rbuffer,regions),'<u8').reshape(-1,8);footprints={};palettes={};owner_alpha=0. if list(key)==a else 1.;source_labels=np.zeros((160,240,4),np.uint8)
  for rec in records:source_labels[int(rec[0])//240,int(rec[0])%240]=label(int(rec[2]),int(rec[3]))
  try:
   for alpha in ([0.,.5] if owner_alpha==0 else [1.]):
    meshes=[]
    try:
     for ri,v in enumerate(rects):
      epoch,rkind,ordinal,refresh,l,r,t,bt=map(int,v)
      if ordinal not in footprints:
       item=(archive['roadmap'] if kind==2 else archive['wallmap'])[ordinal];keep,bs=make(item['blocks'][:12]);geometry=gd(epoch,item['refresh'],rkind,bs,12,65536);assert geometry;f=fc(geometry,ordinal,refresh,projection,65536);assert f;gf(geometry);footprints[ordinal]=f;palettes[ordinal]=np.broadcast_to(label(rkind,ordinal),(160,256,4)).copy().tobytes()
      output=(D*36)();n=U();assert ring(regions,ri,footprints[ordinal],A,CA,B,CB,alpha,projection,output,C.sizeof(output),C.byref(n));m=mesh(output,n.value,65536);assert m;vtx=np.frombuffer(blob(vertices,m),'<f4').reshape(-1,3,5).astype(float);meshes.append((m,vtx,ordinal,rkind))
     for w,h,aw,ah in [(240,160,240,160),(3840,2160,3240,2160)]:
      rawout=C.create_string_buffer(w*h*4);assert seed(gpu,zero,15136,zero,15136,0,empty_palette,len(empty_palette),w,h,aw,ah,0,0,rawout,len(rawout)),error();expected=np.zeros((h,w,4),np.uint8);uncertain=np.zeros((h,w),bool);xx=(np.arange(aw)+.5)*240/aw;yy=(ah-np.arange(ah)-.5)*160/ah
      for m,triangles,ordinal,rkind in meshes:
       color=label(rkind,ordinal)
       for tri in triangles:
        xy=tri[:,:2];lo=np.maximum([0,0],np.floor([xy[:,0].min()*aw/240-1,(160-xy[:,1].max())*ah/160-1])).astype(int);hi=np.minimum([aw,ah],np.ceil([xy[:,0].max()*aw/240+1,(160-xy[:,1].min())*ah/160+1])).astype(int);lx,ly=lo;rx,ry=hi
        if lx>=rx or ly>=ry:continue
        x=xx[lx:rx][None,:];y=yy[ly:ry,None];edges=[]
        for ei in range(3):
         u=xy[ei];v=xy[(ei+1)%3];cross=(v[0]-u[0])*(y-u[1])-(v[1]-u[1])*(x-u[0]);edges.append(cross);length=np.hypot((v[0]-u[0])*aw/240,(v[1]-u[1])*ah/160);distance=np.abs(cross)*aw*ah/(240*160)/length;uncertain[ly:ry,lx:rx]|=distance<=1/128
        edges=np.array(edges);covered=(edges>=0).all(axis=0)|(edges<=0).all(axis=0);expected[ly:ry,lx:rx][covered]=color
       assert submit(gpu,m,material,palettes[ordinal],163840,aw,ah,(U*4)(0,240,0,160)),error()
      assert read(gpu,rawout,len(rawout)),error();actual=np.frombuffer(rawout.raw,np.uint8).reshape(h,w,4);is_endpoint=alpha==owner_alpha
      if is_endpoint:
       sx=((np.arange(aw,dtype=np.int64)*2+1)*120)//aw;sy=(((ah-np.arange(ah,dtype=np.int64))*2-1)*80)//ah;expected[:ah,:aw]=source_labels[sy[:,None],sx[None,:]]
      differences=np.any(actual!=expected,axis=2);outside=differences&~uncertain;assert not outside.any(),('Unexpected mask raster difference',list(key),kind,alpha,w,int(outside.sum()),np.argwhere(outside)[:5].tolist())
      count=int(differences.sum());bd=int((differences&uncertain).sum());boundary_diff+=bd;boundary+=int(uncertain.sum());compared+=w*h-int(uncertain.sum())
      if is_endpoint:
       full_endpoint_diff+=count
       if w==240:assert count==0,('Original endpoint mask mismatch',list(key),kind,count);native_endpoint_pixels+=w*h
      assert not actual[:ah,aw:].any() and not actual[ah:].any();digest=hashlib.sha256(rawout.raw).hexdigest();rows.append(dict(owner=list(key),kind=kind,alpha=alpha,size=[w,h,aw,ah],regions=len(meshes),endpoint=is_endpoint,pixel_differences=count,boundary_pixels=int(uncertain.sum()),pixel_differences_away_from_boundaries=int(outside.sum()),sha256=digest));print('PASS',key[1],kind,alpha,w,'differences',count,'edge ambiguous',int(uncertain.sum()),flush=True)
      if w==3840 and kind==3:
       path=out/('owner-'+str(key[1])+'-alpha-'+str(alpha)+'-writer-mask-4k.png');Image.fromarray(actual[::-1].copy()).save(path);image_hashes[path.name]=sha(path)
    finally:
     for m,_,_,_ in meshes:mf(m)
  finally:
   for f in footprints.values():ff(f)
   free(regions)
finally:close(gpu);mtf(material)
r=dict(result='PASS_REGION_GPU_WRITER_MASKS_WITH_DECLARED_RASTER_BOUNDARIES',renderer=gpu_name,cases=len(rows),pixels_compared_away_from_raster_boundaries=compared,pixels_in_declared_raster_boundary_region=boundary,pixel_differences_within_boundary_region=boundary_diff,pixel_differences_away_from_boundary_region=0,original_resolution_endpoint_pixels_exact=native_endpoint_pixels,endpoint_full_image_pixel_differences=full_endpoint_diff,unchanged_target_margins=True,rows=rows,diagnostic_images=image_hashes,gpu_dll_sha256=sha(gpuout/'recipe-gpu.dll'),region_dll_sha256=sha(base/'NFSUG-pc-recipe-region-tests/recipe-regions.dll'),gpu_build_report_sha256=sha(gpuout/'recipe-gpu-build-report.json'),region_build_report_sha256=sha(base/'NFSUG-pc-recipe-region-tests/region-build-report.json'),coverage_report_sha256=sha(base/'NFSUG-pc-recipe-coverage-tests/coverage-test-report.json'),source_region_test_sha256=sha(original),executed_input_prefix_sha256=hashlib.sha256(prefix.encode()).hexdigest(),script_sha256=sha(Path(__file__)),scope='Actual writer-labelled coverage masks using constant diagnostic colors, per-rectangle submission order. Independent labelled source bitmap at endpoints and triangle raster oracle at midpoint. Boundary region1/128 target pixel from triangle edges. No material texture/shade/painter-order/full-scene claims.',core_opened=False,full_scene_60fps=False)
(out/'region-gpu-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['rows','diagnostic_images']},indent=2))
