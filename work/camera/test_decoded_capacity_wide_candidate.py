import ctypes as C,json,struct,time,hashlib
from pathlib import Path
p=Path('work/camera');report=json.loads((p/'prototype-runs/owned-native-1791434872973979000.json').read_text());folder=Path(report['live_preparation_profiles'][0]['capture']);materials=[]
for captured_path in sorted(Path('work/camera/prototype-runs').glob('profile-scene-*/older.frame.bin')):
 name=captured_path.name;folder=captured_path.parent
 frame=(folder/name).read_bytes();assert frame[:4]==b'NGF3';n=struct.unpack_from('<I',frame,8)[0];data=frame[40:40+n];off=0
 while off<len(data):
  magic,kind,context,count=struct.unpack_from('<4I',data,off);assert magic==0x3147534e and count==12;off+=16;blocks=[]
  for _ in range(12):
   size=struct.unpack_from('<I',data,off)[0];off+=4;blocks.append(data[off:off+size]);off+=size
  if kind==1:shift,h=struct.unpack_from('<HH',blocks[3],36);h//=2;src,pal,tr=blocks[7],blocks[8],0;stride=2*(1<<shift)
  elif kind==2:shift,h=struct.unpack_from('<HH',blocks[4],36);src,pal,tr=blocks[8],blocks[9],1;stride=1<<shift
  elif kind==3:shift,h=struct.unpack_from('<HH',blocks[0],56);src,pal,tr=blocks[10],blocks[11],0;stride=1<<shift
  else:raise AssertionError(kind)
  w=1<<shift;assert len(src)>=stride*h and len(pal)==512;materials.append((w,h,stride,src,pal,tr))
 assert off==len(data)
libs=[]
for capacity in (32,64):
 d=C.CDLL(str((p/f'decoded-capacity-{capacity}-candidate.dll').resolve()));d.decode.argtypes=[C.c_uint]*3+[C.c_void_p]*2+[C.c_uint,C.c_void_p,C.c_size_t];d.nf_owned_decoded_texture_stats.argtypes=[C.c_void_p];libs.append(d)
counts=[0,0];times=[[],[]];digest=hashlib.sha256()
try:
 for repeat in range(2):
  for w,h,stride,src,pal,tr in materials:
   outputs=[]
   for j,d in enumerate(libs):
    out=C.create_string_buffer(w*h*4);begin=time.perf_counter_ns();assert d.decode(w,h,stride,src,pal,tr,out,len(out))==1;times[j].append(time.perf_counter_ns()-begin);outputs.append(out.raw);counts[j]+=1
   assert outputs[0]==outputs[1];digest.update(outputs[0])
 stats=[]
 for d in libs:
  v=(C.c_uint64*3)();d.nf_owned_decoded_texture_stats(v);assert v[2]<=16*1024*1024;stats.append(dict(hits=v[0],misses=v[1],bytes=v[2]))
finally:
 for d in libs:d.clear();v=(C.c_uint64*3)();d.nf_owned_decoded_texture_stats(v);assert v[2]==0
out=dict(result='PASS_WIDE_CAPTURED_MATERIAL_CAPACITY_RGBA_PARITY',captured_records=len(materials),calls=counts,rgba_sha256=digest.hexdigest(),capacity32=stats[0],capacity64=stats[1],scope='Independent captured older endpoints concatenated by folder timestamp and repeated twice; artificial request order, includes all packet materials regardless of visibility. Exact expanded RGBA and byte-budget/clear verification; no full4K, live cost, eviction stress or smooth60 proof.')
(p/'prototype-runs/decoded-capacity-wide-20261009.json').write_text(json.dumps(out,indent=2));print(out)
