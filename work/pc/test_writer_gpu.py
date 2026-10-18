from pathlib import Path
import os,ctypes as C,json,struct,zlib,hashlib
import numpy as np
from PIL import Image
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-writer-gpu-tests'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# Verified region geometry inputs, before drawing any mask case.
original=here/'test_region_mask_gpu.py';boot=original.read_text().split('try:\n for name,h in cr[')[0].replace('NFSUG-pc-region-mask-tests','NFSUG-pc-writer-gpu-tests');geo={'__file__':str(original),'__name__':'writer_geometry_inputs'};exec(compile(boot,str(original),'exec'),geo)
# Verified original integer sampler and all canonical archive keys, without its tests.
reference=here/'test_recipe_writer.py';prefix=reference.read_text().split('writer_cases=cells=')[0];ref={'__file__':str(reference),'__name__':'writer_reference_inputs'};exec(compile(prefix,str(reference),'exec'),ref)
P=geo['P'];S=geo['S'];Q=geo['Q'];U=geo['U'];D=geo['D'];fn=geo['fn'];d=geo['d'];gpu=geo['gpu'];make=ref['make'];blob=ref['blob'];env=geo['env'];archive=geo['archive'];A=geo['A'];B=geo['B'];CA=geo['CA'];CB=geo['CB'];projection=geo['projection'];a=geo['a'];recipes=ref['recipes'];cr=ref['cr']
op=fn(d,'nf_pc_recipe_writer_decode',[P,U,Q,U,P,U,S],P);wf=fn(d,'nf_pc_recipe_writer_free',[P],None);amap=fn(d,'nf_pc_writer_address_map',[P,S],P);af=fn(d,'nf_pc_writer_address_map_free',[P],None);ai=fn(d,'nf_pc_writer_address_map_info',[P,P]);ab=fn(d,'nf_pc_writer_address_map_buffer',[P,P,P]);draw=fn(d,'nf_pc_scene_gpu_render_writer',[P,P,U,P,P,P,P,S,U,U,U,U]);mesh=env['mesh'];mf=env['mf'];ring=geo['ring'];
y,index=np.indices((160,256));palette=np.empty((160,256,4),np.uint8);palette[:,:,0]=index;palette[:,:,1]=(index*13+y*7)%256;palette[:,:,2]=(index*29+y*31)%256;palette[:,:,3]=(index+y)%256;pb=palette.tobytes();rows=[];compared=uncertain_total=boundary_differences=endpoint_pixels=map_bytes=reference_cells=bindings=0;images={}
try:
 for name,h in cr['fixture_sha256'].items():
  path=base/'NFSUG-pc-recipe-coverage-tests'/name;assert sha(path)==h;raw=zlib.decompress(path.read_bytes()[8:]);fields=struct.unpack_from('<5Q4I',raw);key=(Q*5)(*fields[:5]);kind,top,bottom,hn=fields[5:];c=geo['cover'](raw[56:56+hn],hn,raw[56+hn:],192080,key,kind,top,bottom,64*1024*1024);assert c;records=np.frombuffer(blob(geo['cbuffer'],c,2),'<u8').reshape(-1,6).copy();regions=geo['create'](c,64*1024*1024);assert regions;geo['cf'](c);rects=np.frombuffer(blob(geo['rbuffer'],regions),'<u8').reshape(-1,8);prepared={};footprints={};source_index=np.zeros((160,240),np.uint8);source_write=np.zeros((160,240),bool)
  for row in records:source_index[int(row[0])//240,int(row[0])%240]=row[5];source_write[int(row[0])//240,int(row[0])%240]=True
  owner_alpha=0. if list(key)==a else 1.
  try:
   for ordinal in sorted(set(map(int,records[:,3]))):
    values,write=recipes[(kind-1,ordinal)];keep,bs=make(values);w=op(key,kind-1,ordinal,write,bs,15,64*1024*1024);old=ref['op'](key,kind-1,ordinal,write,bs,15,64*1024*1024);assert w and old;address=amap(w,64*1024*1024);assert address;meta=(Q*15)();assert ai(address,meta);left,right,topmap,bottom=map(int,meta[9:13]);packed=blob(ab,address);offsets=np.frombuffer(packed,'<u4').reshape(bottom-topmap,right-left);ri=np.zeros(offsets.shape,np.uint8);rs=np.zeros(offsets.shape,bool)
    try:
     for yy in range(topmap,bottom):
      for xx in range(left,right):
       result=(Q*4)();assert ref['sample'](old,xx,yy,result);encoded=int(offsets[yy-topmap,xx-left]);assert encoded==(result[0]+1 if result[3] else 0),('Address descriptor differs',kind,ordinal,xx,yy,encoded,list(result));ri[yy-topmap,xx-left]=result[2];rs[yy-topmap,xx-left]=bool(result[3]);reference_cells+=1
    finally:ref['free'](old)
    prepared[ordinal]=(w,address,left,right,topmap,bottom,ri,rs);map_bytes+=len(packed);bindings+=1
   for alpha in ([0.,.5] if owner_alpha==0 else [1.]):
    meshes=[]
    try:
     for rectangle,v in enumerate(rects):
      epoch,rkind,ordinal,write,l,r,t,bt=map(int,v)
      if ordinal not in footprints:
       item=(archive['roadmap'] if kind==2 else archive['wallmap'])[ordinal];keep,bs=make(item['blocks'][:12]);geometry=geo['gd'](epoch,item['refresh'],rkind,bs,12,65536);assert geometry;f=geo['fc'](geometry,ordinal,write,projection,65536);assert f;geo['gf'](geometry);footprints[ordinal]=f
      output=(D*36)();n=U();assert ring(regions,rectangle,footprints[ordinal],A,CA,B,CB,alpha,projection,output,C.sizeof(output),C.byref(n));rawring=np.array(output[:n.value*6]).reshape(-1,6);m=mesh(output,n.value,65536);assert m;triangles=np.frombuffer(blob(geo['vertices'],m),'<f4').reshape(-1,3,5).astype(float);mf(m);X=np.column_stack([np.ones(len(rawring)),rawring[:,:2]]);values=np.column_stack([rawring[:,3]*rawring[:,5],rawring[:,4]*rawring[:,5],rawring[:,5]]);H=np.linalg.lstsq(X,values,rcond=None)[0];meshes.append((output,n.value,(U*4)(l,r,t,bt),triangles,H,ordinal))
     for w,h,aw,ah in [(240,160,240,160),(3840,2160,3240,2160)]:
      for index_mode in [1,0]:
       pixels=C.create_string_buffer(w*h*4);assert geo['seed'](gpu,geo['zero'],15136,geo['zero'],15136,0,geo['empty_palette'],163840,w,h,aw,ah,0,0,pixels,len(pixels));expected=np.zeros((h,w,4),np.uint8);uncertain=np.zeros((h,w),bool);xx=(np.arange(aw)+.5)*240/aw;yy=(ah-np.arange(ah)-.5)*160/ah
       for output,n,bounds,triangles,H,ordinal in meshes:
        writer,address,left,right,topmap,bottom,ref_index,ref_write=prepared[ordinal]
        for tri in triangles:
         xy=tri[:,:2];lo=np.maximum([0,0],np.floor([xy[:,0].min()*aw/240-1,(160-xy[:,1].max())*ah/160-1])).astype(int);hi=np.minimum([aw,ah],np.ceil([xy[:,0].max()*aw/240+1,(160-xy[:,1].min())*ah/160+1])).astype(int);lx,ly=lo;rx,ry=hi
         if lx>=rx or ly>=ry:continue
         x=xx[lx:rx][None,:];y=yy[ly:ry,None];edges=[]
         for ei in range(3):
          p=xy[ei];q=xy[(ei+1)%3];cross=(q[0]-p[0])*(y-p[1])-(q[1]-p[1])*(x-p[0]);edges.append(cross);length=np.hypot((q[0]-p[0])*aw/240,(q[1]-p[1])*ah/160);uncertain[ly:ry,lx:rx]|=np.abs(cross)*aw*ah/(240*160)/length<=1/128
         edges=np.array(edges);inside=(edges>=0).all(axis=0)|(edges<=0).all(axis=0);hom=H[0]+x[:,:,None]*H[1]+y[:,:,None]*H[2];st=hom[:,:,:2]/hom[:,:,2,None]
         for axis in range(2):
          nearest=np.rint(st[:,:,axis]);distance=np.abs(hom[:,:,axis]-nearest*hom[:,:,2])/np.maximum(np.hypot((H[1,axis]-nearest*H[1,2])*240/aw,(H[2,axis]-nearest*H[2,2])*160/ah),1e-30);uncertain[ly:ry,lx:rx]|=inside&(distance<=1/128)
         sx=np.floor(st[:,:,0]).astype(int);sy=np.floor(st[:,:,1]).astype(int);valid=inside&(sx>=left)&(sx<right)&(sy>=topmap)&(sy<bottom);ix=np.clip(sx-left,0,max(0,right-left-1));iy=np.clip(sy-topmap,0,max(0,bottom-topmap-1));valid&=ref_write[iy,ix];vy,vx=np.nonzero(valid);indices=ref_index[iy[vy,vx],ix[vy,vx]];target_y=vy+ly;target_x=vx+lx;expected[target_y,target_x,3]=255
         if index_mode:expected[target_y,target_x,0]=indices
         else:source_y=(((ah-target_y)*2-1)*80)//ah;expected[target_y,target_x,:3]=palette[source_y,indices,:3]
        assert draw(gpu,output,n,bounds,writer,address,pb,len(pb),aw,ah,int(alpha==owner_alpha),index_mode),geo['error']()
       is_endpoint=alpha==owner_alpha
       if is_endpoint:
        sx=((np.arange(aw,dtype=np.int64)*2+1)*120)//aw;sy=(((ah-np.arange(ah,dtype=np.int64))*2-1)*80)//ah;inside=source_write[sy[:,None],sx[None,:]];indices=source_index[sy[:,None],sx[None,:]];expected[:ah,:aw]=0;iy,ix=np.nonzero(inside);expected[iy,ix,3]=255
        if index_mode:expected[iy,ix,0]=indices[iy,ix]
        else:expected[iy,ix,:3]=palette[sy[iy],indices[iy,ix],:3]
       assert geo['read'](gpu,pixels,len(pixels));actual=np.frombuffer(pixels.raw,np.uint8).reshape(h,w,4);diff=np.any(actual!=expected,axis=2);bad=diff&~uncertain;assert not bad.any(),('Writer GPU sample differs',key[1],kind,alpha,w,index_mode,int(bad.sum()),np.argwhere(bad)[:5].tolist());differences=int(diff.sum());boundary_differences+=int((diff&uncertain).sum());compared+=w*h-int(uncertain.sum());uncertain_total+=int(uncertain.sum())
       if is_endpoint:assert differences==0,('Endpoint writer indices/colors must be exact',key[1],kind,w,index_mode,differences);endpoint_pixels+=w*h
       assert not actual[:ah,aw:].any();rows.append(dict(owner=list(key),kind=kind,alpha=alpha,size=[w,h,aw,ah],index_mode=index_mode,endpoint=is_endpoint,differences=differences,uncertain_pixels=int(uncertain.sum())));print('PASS',key[1],kind,alpha,w,index_mode,'diff',differences,flush=True)
       if w==3840 and kind==3 and not index_mode:path=out/('owner-'+str(key[1])+'-alpha-'+str(alpha)+'-writer-textures-4k.png');Image.fromarray(actual[::-1].copy()).save(path);images[path.name]=sha(path)
    finally:pass
  finally:
   for f in footprints.values():geo['ff'](f)
   for writer,address,*_ in prepared.values():af(address);wf(writer)
   geo['free'](regions)
finally:geo['close'](gpu);geo['mtf'](geo['material'])
build=json.loads((out/'recipe-gpu-build-report.json').read_text());r=dict(result='PASS_RAW_WRITER_TEXTURES_IN_PROJECTIVE_GPU_MASKS',cases=len(rows),writer_bindings=bindings,address_descriptor_bytes=map_bytes,native_reference_cells=reference_cells,pixels_compared_away_from_declared_boundaries=compared,declared_boundary_pixels=uncertain_total,differences_within_declared_boundaries=boundary_differences,pixel_differences_outside_declared_boundaries=0,endpoint_pixels_exact=endpoint_pixels,rows=rows,diagnostic_images=images,gpu_dll_sha256=sha(out/'recipe-gpu.dll'),build_report_sha256=sha(out/'recipe-gpu-build-report.json'),writer_reference_test_sha256=sha(reference),region_input_test_sha256=sha(original),script_sha256=sha(Path(__file__)),scope='Original integer writer sample locations transported on world supports, raw source texture fetch and effective shade; source-address descriptors contain no cached colors/indices. Exact endpoint indices plus synthetic row-palette colors. Midpoint uncertainty1/128 target pixel from mask/owner-cell boundaries. Not authored subpixel UV or final native4K texture quality/full-scene order.',core_opened=False,full_scene_60fps=False)
(out/'writer-gpu-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['rows','diagnostic_images']},indent=2))
