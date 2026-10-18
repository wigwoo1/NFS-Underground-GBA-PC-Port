from pathlib import Path
import ctypes as C,os,struct,json,hashlib,math
import numpy as np
source=Path(__file__).parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-world-gpu-tests'
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'world-gpu.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;I=C.c_int

def fn(n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
op=fn('nf_pc_world_gpu_open',[],P);close=fn('nf_pc_world_gpu_close',[P],None);draw=fn('nf_pc_world_gpu_draw',[P,P,P,P,S,U,U,U,U,U,U,P,S]);error=fn('nf_pc_world_gpu_error',[],C.c_char_p);read=fn('nf_pc_world_decode',[P,S,S],P);wf=fn('nf_pc_world_free',[P],None);mesh=fn('nf_pc_world_mesh',[P,U,S],P);mf=fn('nf_pc_world_mesh_free',[P],None);material=fn('nf_pc_world_material',[P,U,S],P);tf=fn('nf_pc_world_material_free',[P],None)
original=(base/'NFSUG-pc-world-material-tests/inputs/synthetic-mode-0.nsp').read_bytes();parts=[]
for i in range(5):at,n=struct.unpack_from('<2I',original,36+i*12);parts.append(original[at:at+n])

def packet(mode,wall,state,alpha):
 points=[(-120,-80,64),(120,-80,64),(120,80,64),(-120,80,64)];surface=struct.pack('<3I',4,1,1)+b''.join(struct.pack('<3d',*v) for v in points)+struct.pack('<8d',*[.25]*8)+bytes([21,42,63,alpha]);lit=mode in [3,8]
 if lit:states=bytes([0 if state==0 else 2]+[state]*16);indices=bytes([0 if state==0 else 1]+[level+1 if state==2 else 0 for level in range(16)]) if mode==8 else b'';metadata=states+indices
 elif mode==2:metadata=bytes([state])
 elif mode==1:metadata=bytes([0])
 else:metadata=b''
 world=struct.pack('<2I',0x31444652,1)+surface+struct.pack('<4I',0x3149574e,1,mode,len(metadata))+metadata;light=struct.pack('<3I',0x314c464e,1,int(lit))+(struct.pack('<4I',0,15,1,1)+b''.join(bytes([level,42,63,17]) for level in range(16)) if lit else b'')+parts[3][-131072:];identity=struct.pack('<2I',0x3149464e,2)+struct.pack('<10I',2 if wall else 1,1,2,3,4,3,5,6,7,8)+struct.pack('<2Id8H',0x3242464e,2,0.,20,200,3,157,0,240,0,160);sections=[parts[0],world,parts[2],light,identity];raw=bytearray(original[:92]);struct.pack_into('<I',raw,8,92+sum(map(len,sections)))
 for i,part in enumerate(sections):struct.pack_into('<3I',raw,32+i*12,i+1,len(raw),len(part));raw+=part
 return bytes(raw)
pal=np.zeros((160,256,4),np.uint8);pal[:,:,0]=np.arange(256,dtype=np.uint8)[None,:];pal[:,:,1]=np.arange(160,dtype=np.uint8)[:,None];pal[:,:,2]=77;pal[:,:,3]=255;palette=pal.tobytes();ctx=op();assert ctx;rows=[]
try:
 for label,mode,wall,state,alpha in [('wall-skip',2,True,0,255),('lit-rgba-zero',3,True,1,255),('lit-rgba-color',3,True,2,255),('lit-index-zero',8,True,1,255),('lit-index-color',8,True,2,255),('opaque-road-index-zero',1,False,2,0),('road-rgba-zero',0,False,2,0),('wall-rgba-skip',0,True,2,0)]:
  raw=packet(mode,wall,state,alpha);world=read(raw,len(raw),64*1024*1024);assert world;geometry=mesh(world,0,32*1024*1024);texture=material(world,0,64*1024*1024);assert geometry and texture;wf(world)
  try:
   for w,h,aw,ah,top,bottom in [(240,160,240,160,0,160),(3840,2160,3240,2160,53,107)]:
    output=(C.c_ubyte*(w*h*4))();assert draw(ctx,geometry,texture,palette,len(palette),w,h,aw,ah,top,bottom,output,len(output)),error();a=np.frombuffer(output,np.uint8).reshape(h,w,4);expected=np.zeros_like(a);left=math.ceil(20*aw/240-.5);right=math.ceil(200*aw/240-.5);t=math.ceil(max(3,top)*ah/160-.5);b=math.ceil(min(157,bottom)*ah/160-.5)
    skip=wall and ((mode==2 and state==0) or (mode==0 and alpha==0))
    if not skip:
     ys=((ah-np.arange(ah))*2-1)*80//ah;xs=np.arange(aw);shade=((xs*2+1)*15)//(aw*2)
     if mode==3 and state==2:colors=np.broadcast_to(np.stack([shade,np.full(aw,42),np.full(aw,63),np.full(aw,255)],axis=1).astype(np.uint8),(ah,aw,4))
     else:index=shade+1 if mode==8 and state==2 else np.zeros(aw,dtype=int);colors=pal[ys[:,None],index[None,:]]
     expected[ah-b:ah-t,left:right]=colors[ah-b:ah-t,left:right]
    assert np.array_equal(a,expected),(label,w,int(np.any(a!=expected,axis=2).sum()));rows.append(dict(case=label,width=w,height=h,pixels=w*h,exact=True,sha256=hashlib.sha256(output).hexdigest()))
  finally:mf(geometry);tf(texture)
finally:close(ctx)
r=dict(result='PASS_PC_WORLD_GPU_EXACT_CONTRACTS',cases=len(rows),pixel_comparisons=sum(r['pixels'] for r in rows),all_pixels_exact=True,source_bounds_and_owner_rows=True,all_wall_write_states=True,rgba_and_indexed_palette_zero=True,per_column_lit_shading=True,source_world_freed_before_render=True,dll_sha256=hashlib.sha256((out/'world-gpu.dll').read_bytes()).hexdigest(),test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),frames=rows,full_scene=False,full_scene_60fps=False)
(out/'world-gpu-contract-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='frames'},indent=2))
