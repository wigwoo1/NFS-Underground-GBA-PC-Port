from pathlib import Path
import struct,subprocess,json,random,ctypes as C,numpy as np,sys
wall_writes='--wall-writes' in sys.argv
zero_coverage='--zero-coverage' in sys.argv
p=Path('work/camera').resolve();data=(p/'hud-batch-captured.bin').read_bytes();rng=random.Random(15173);reports=[]
for case in range(8):
 rows=[]
 for y in range(160):
  row=bytearray(data[y*34944:(y+1)*34944]);display=struct.unpack_from('<H',row,8)[0]|(rng.randrange(4)<<13)
  window=[rng.randrange(65536) for _ in range(6)];blend=rng.randrange(65536)&0x3fff
  if case==0:
   display=0x3044;window=[0x0101,0,0x00a0,0,32,0];blend=0xa0
  if case==1:
   display=0x7044;window=[0xc814,0x0a96,0x00a0,0x8c14,0x203f,0x14];blend=0xff
  struct.pack_into('<H',row,8,display);struct.pack_into('<6H',row,72,*window);struct.pack_into('<H',row,88,blend);struct.pack_into('<H',row,90,rng.randrange(65536));struct.pack_into('<H',row,92,rng.randrange(32));struct.pack_into('<H',row,20,rng.randrange(4))
  rows.append(row)
 source=p/f'hud-windows-{case}.bin';source.write_bytes(b''.join(rows));target=p/f'hud-windows-{case}.rgba';ref=p/f'hud-windows-{case}-cpu.rgba'
 subprocess.check_call([str(p/'hud-gpu-batched.exe'),str(source),str(target),str(ref)]+(['--wall-writes'] if wall_writes else ['--zero-coverage'] if zero_coverage else []))
 actual=np.fromfile(target,np.uint32).reshape(2160,3840)[::-1];expected=np.fromfile(ref,np.uint32).reshape(2160,3840);diff=actual!=expected
 assert not diff.any(),(case,int(diff.sum()),np.argwhere(diff)[:8].tolist())
 reports.append(dict(case=case,checked_pixels=3840*2160))
d=C.CDLL(str(p/'obj-tile.dll'));f=d.nf_obj_window_scanline_prepared;f.argtypes=[C.c_void_p,C.c_size_t]*3+[C.c_uint16,C.c_uint,C.c_void_p,C.c_uint,C.c_uint]+[C.c_void_p]*4
b=data[:34944];v=bytes(65536)+b[128:32896];pal=b[32896:33920];o=b[33920:];window=(C.c_uint16*6)();outputs=[C.create_string_buffer(bytes([65+i])*size,size) for i,size in enumerate((960,960,240,240))];saved=[x.raw for x in outputs]
for display,row in ((0x1044,160),(0x9044,0)):
 assert not f(v,len(v),pal,len(pal),o,len(o),display,row,window,0x3f3f,8,*outputs)
 assert [x.raw for x in outputs]==saved
r=dict(result='PASS',samples=reports,atomic_window_scanline_rejections=2,zero_background_coverage=zero_coverage,actual_wall_writer=wall_writes,scope='Exact GPU rectangular-window OBJ/world/effect gating vs full native window/candidate composition; empty-span backdrop alignment, wrapped/overlapping/out-of-range scanline windows; synthetic world background, not broad live transitions or scanout')
if wall_writes:r['scope']='Actual three-state wall GPU writer over earlier opaque geometry followed by actual live HUD composition, exact versus independent CPU pixel expectations; synthetic geometry/captured HUD, no full-scene or scanout proof.'
(p/('hud-wall-writes-gpu-tests.json' if wall_writes else 'hud-windows-zero-gpu-tests.json' if zero_coverage else 'hud-windows-gpu-tests.json')).write_text(json.dumps(r,indent=2));print(r)
