import ctypes as C,random,json,struct
from pathlib import Path
p=Path('work/camera');base=C.CDLL(str((p/'hud-window-baseline-candidate.dll').resolve()));direct=C.CDLL(str((p/'hud-plane-candidate.dll').resolve()))
a=base.nf_obj_window_scanline_prepared;b=direct.nf_obj_plane_window_scanline_prepared
args=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_uint16,C.c_uint,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
a.argtypes=b.argtypes=args
k=C.WinDLL('kernel32',use_last_error=True);k.VirtualAlloc.argtypes=[C.c_void_p,C.c_size_t,C.c_uint,C.c_uint];k.VirtualAlloc.restype=C.c_void_p;k.VirtualProtect.argtypes=[C.c_void_p,C.c_size_t,C.c_uint,C.c_void_p];k.VirtualFree.argtypes=[C.c_void_p,C.c_size_t,C.c_uint]
address=k.VirtualAlloc(None,36864,0x3000,4);assert address;old=C.c_uint();assert k.VirtualProtect(address+32768,4096,1,C.byref(old))
rng=random.Random(1049);checked=0
try:
 for trial in range(400):
  plane=rng.randbytes(32768);C.memmove(address,plane,32768);v=C.create_string_buffer(bytes(65536)+plane);palette=C.create_string_buffer(rng.randbytes(1024));o=bytearray(1024)
  for i in range(128):struct.pack_into('<H',o,i*8,512)
  for i in range(8):
   affine=rng.randrange(2);attr=(rng.randrange(3)<<14)|(rng.randrange(2)<<13)|(affine<<8)|rng.randrange(256)
   if affine:attr|=rng.randrange(2)<<9
   pos=(rng.randrange(4)<<14)|rng.randrange(512)|(rng.randrange(32)<<9 if affine else rng.randrange(4)<<12)
   tile=rng.choice([0,511,512,1022,1023]);color=(rng.randrange(16)<<12)|(rng.randrange(4)<<10)|tile
   struct.pack_into('<3H',o,i*8,attr,pos,color)
  # Affine matrix slots remain captured OAM bytes; negative coefficients exercise wraps.
  for i in range(32):
   for j in range(4):struct.pack_into('<h',o,i*32+6+j*8,rng.randrange(-512,513))
  ob=C.create_string_buffer(bytes(o));window=(C.c_uint16*6)(*[rng.randrange(65536) for _ in range(6)]);display=4|0x1000|rng.choice([0,64])|rng.choice([0,0x2000,0x4000,0x6000]);row=rng.randrange(160);blend=rng.randrange(16384);bright=rng.randrange(32)
  outs=[];statuses=[]
  for fn,ptr,n in [(a,C.cast(v,C.c_void_p),98304),(b,address,32768)]:
   colors=C.create_string_buffer(bytes([165])*960);tags=C.create_string_buffer(bytes([165])*960);control=C.create_string_buffer(bytes([165])*240);backdrop=C.create_string_buffer(bytes([165])*240)
   statuses.append(fn(ptr,n,palette,1024,ob,1024,display,row,window,blend,bright,colors,tags,control,backdrop));outs.append(colors.raw+tags.raw+control.raw+backdrop.raw)
  assert statuses[0]==statuses[1] and outs[0]==outs[1],trial;checked+=1
 # Reject a short plane before output/read; protected page starts directly after full plane.
 out=C.create_string_buffer(bytes([165])*2400);before=out.raw
 assert b(address,32767,palette,1024,ob,1024,display,row,window,blend,bright,out,C.byref(out,960),C.byref(out,1920),C.byref(out,2160))==0 and out.raw==before
finally:assert k.VirtualFree(address,0,0x8000)
result=dict(result='PASS_DIRECT_OBJ_PLANE_EDGES_GUARD',cases=checked,short_plane_atomic_rejection=True,guard_page_after_32k=True,scope='Deterministic synthetic affine/regular shapes/tilewrap/windows/priority/palette plus captured parity separate; component only.')
(p/'prototype-runs/hud-plane-edges-20261009.json').write_text(json.dumps(result,indent=2));print(result)
