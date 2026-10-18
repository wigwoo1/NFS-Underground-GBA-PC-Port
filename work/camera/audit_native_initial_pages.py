from pathlib import Path
import ctypes as C,struct,json
from scene_batches import batches
p=Path('work/camera');d=C.CDLL(str((p/'native_initial_page.dll').resolve()))
d.nfs_initial_fill.argtypes=[C.c_void_p,C.c_size_t,C.c_uint32,C.c_uint32,C.c_uint32]
d.nfs_initial_copy.argtypes=[C.c_void_p,C.c_size_t,C.c_uint32,C.c_void_p,C.c_size_t]+[C.c_uint32]*4
original=list(batches(p/'motion-original-source-8750-8781.bin'));actual=json.loads((p/'motion-draw-page-tests.json').read_text())['draws'];checks=[]
for scene in batches(p/'motion-original-initial-inputs-world.bin'):
 key=(scene['begin_refresh'],scene['end_refresh'])
 if not (8753<=key[0] and key[1]<=8779):continue
 ref=next(b for b in original if (b['begin_refresh'],b['end_refresh'])==key)
 first=next(e for e in ref['events'] if e['pc'] in (0x030032f0,0x03000304,0x03004770));baseline=Path(actual[str(first['id'])]['before_path']).read_bytes();native=C.create_string_buffer(len(baseline));mask=bytearray(len(baseline));calls=[]
 for e in scene['events']:
  if e['pc']!=0xffff0095:continue
  pc,_,_=struct.unpack('<3I',e['blocks'][95][1]);r=e['regs'];off=r[0]-0x06000000
  if pc==0x030002c0:
   assert d.nfs_initial_fill(native,len(baseline),off,r[1],r[2]);n=(r[2]>>5)*32;mask[off:off+n]=bytes([1])*n
  else:
   ss,ds=struct.unpack('<2I',e['blocks'][96][1]);src=e['blocks'][97][1];assert d.nfs_initial_copy(native,len(baseline),off,src,len(src),r[2],r[3],ss,ds)
   n=((r[2]>>5)+1)*32
   for row in range(r[3]):a=off+row*(ds&~3);mask[a:a+n]=bytes([1])*n
  calls.append(hex(pc))
 page=first['blocks'][3][1] if 3 in first['blocks'] else b''
 mismatches=[i for i,(a,b) in enumerate(zip(native.raw,baseline)) if mask[i] and a!=b];assert not mismatches,(key,mismatches[:5])
 checks.append(dict(begin=key[0],end=key[1],calls=calls,written_bytes=sum(mask),written_bytes_exact=True,retained_bytes=len(mask)-sum(mask),retained_nonzero=sum(b!=0 for i,b in enumerate(baseline) if not mask[i]),scope='Only producer-written bytes compared; retained bytes excluded explicitly.'))
report=dict(result='PASS_NATIVE_INITIAL_WRITTEN_REGIONS',scenes=len(checks),checks=checks);assert len(checks)==7
(p/'native-initial-page-region-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
