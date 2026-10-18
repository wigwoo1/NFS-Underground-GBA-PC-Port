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
 d=C.CDLL(str((p/('decoded-capacity-32-candidate.dll' if capacity==32 else 'decoded-palette-table-candidate.dll')).resolve()));d.decode.argtypes=[C.c_uint]*3+[C.c_void_p]*2+[C.c_uint,C.c_void_p,C.c_size_t];d.nf_owned_decoded_texture_stats.argtypes=[C.c_void_p];libs.append(d)
import statistics
trials=[]
def counters(d):
 v=(C.c_uint64*3)();d.nf_owned_decoded_texture_stats(v);return list(v)
# Keep identical source and output owners alive across each timed request.
requests=[(w,h,stride,src,pal,tr,C.create_string_buffer(w*h*4)) for w,h,stride,src,pal,tr in materials]
for pair in range(8):
 row={}
 for j in ((0,1) if pair%2==0 else (1,0)):
  d=libs[j];d.clear();before=counters(d);costs=[];dig=hashlib.sha256()
  try:
   for repeat in range(3):
    begin=time.perf_counter_ns()
    for w,h,stride,src,pal,tr,output in requests:assert d.decode(w,h,stride,src,pal,tr,output,len(output))==1
    costs.append(time.perf_counter_ns()-begin)
    for *_,output in requests:dig.update(output.raw)
   after=counters(d);assert after[2]<=16*1024*1024
   row[str((32,64)[j])]=dict(median_sequence_ms=statistics.median(costs)/1e6,hits=after[0]-before[0],misses=after[1]-before[1],bytes=after[2],rgba_sha256=dig.hexdigest())
  finally:d.clear();assert counters(d)[2]==0
 assert row['32']['rgba_sha256']==row['64']['rgba_sha256'];trials.append(row)
out=dict(variant_labels={'32':'original32','64':'palette_table32'},result='MATCHED_PALETTE_TABLE_COST',records=len(requests),paired_trials=len(trials),trials=trials,median_trial_ms={k:statistics.median(x[k]['median_sequence_ms'] for x in trials) for k in ('32','64')},scope='Eight alternating serial pairs with identical captured material requests, three sequences per variant, preallocated identical owner lifetimes, exact final output hashes and budget/clear checks. Constructed endpoint sequence, not live scene requests or fullrenderer performance.')
(p/'prototype-runs/decoded-palette-table-matched-cost-20261009.json').write_text(json.dumps(out,indent=2));print(out['median_trial_ms'])
