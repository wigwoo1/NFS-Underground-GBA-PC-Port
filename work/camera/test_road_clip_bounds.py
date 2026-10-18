from pathlib import Path
import ctypes as C,random,json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));fn=d.nf_road_clip_bounds;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
r=random.Random(731);rejections=0
for case in range(500):
 inherited=(C.c_uint16*4)(0,238,0,r.randrange(140,159));fb=(C.c_uint32*4)(0x06000000,0,0,240);count=r.randrange(0,30);spans=(C.c_uint32*(max(1,count)*20))();end=0
 for i in range(count):
  doubled=r.randrange(2);y=r.randrange(160-doubled);x=r.randrange(120);width=r.randrange(1,121-x);spans[i*20]=fb[0]+y*240+x*2;spans[i*20+1]=width;spans[i*20+3]=doubled;end=max(end,y+1+doubled)
 out=(C.c_uint16*4)(999,999,999,999);result=C.c_uint(999);assert fn(inherited,fb,spans,count,out,C.byref(result));assert list(out)==[0,238,0,max(inherited[3],end)] and result.value==end
 if count:
  saved=spans[0];spans[0]=fb[0]+38400;out=(C.c_uint16*4)(999,999,999,999);result.value=999
  assert not fn(inherited,fb,spans,count,out,C.byref(result)) and list(out)==[999]*4 and result.value==999;spans[0]=saved;rejections+=1
padding_cases=0;padding_rejections=0
inherited=(C.c_uint16*4)(0,238,0,158);fb=(C.c_uint32*4)(0x06000000,0,0,240)
for y,x,width,doubled in ((158,0,121,1),(159,0,121,1),(10,238,2,0)):
 spans=(C.c_uint32*20)(fb[0]+y*240+x,width,0,doubled);out=(C.c_uint16*4)();end=C.c_uint()
 written_rows={((y*240+x+byte+copy*240)//240) for copy in range(doubled+1) for byte in range(width*2)};expected=min(160,max(written_rows)+1)
 assert fn(inherited,fb,spans,1,out,C.byref(end)) and end.value==expected and out[3]==max(158,end.value);padding_cases+=1
for y,x,width,doubled in ((160,0,121,0),(10,0,122,0),(10,239,1,0),(10,238,3,0),(10,0,1,2)):
 spans=(C.c_uint32*20)(fb[0]+y*240+x,width,0,doubled);out=(C.c_uint16*4)(999,999,999,999);end=C.c_uint(999)
 assert not fn(inherited,fb,spans,1,out,C.byref(end)) and list(out)==[999]*4 and end.value==999;padding_rejections+=1
report=dict(result='PASS',cases=500,right_padding_and_bottom_cap_cases=padding_cases,excess_padding_atomic_rejections=padding_rejections,atomic_invalid_framebuffer_rejections=rejections,scope='Native bounds generation from synthetic valid20word spans; atomic out-of-frame rejection. Scene parity tested separately.')
(p/'road-clip-bounds-tests.json').write_text(json.dumps(report,indent=2));print(report)

