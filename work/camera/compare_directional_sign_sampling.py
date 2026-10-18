"""Compare actual sign column texels with recovered continuous world projection."""
import ctypes as C,collections,hashlib,json,math,struct,sys
from pathlib import Path
from scene_batches import batches
capture_path=Path(sys.argv[1]);capture=json.loads(capture_path.read_text());trace=Path(capture['trace']);assert hashlib.sha256(trace.read_bytes()).hexdigest()==capture['trace_sha256'];projection=json.loads(Path(sys.argv[2]).read_text());poses={tuple(r['interval']):r for r in projection['checks']};checks=[]
d=C.CDLL(str((Path('work/camera')/'native_wall.dll').resolve()));fn=d.nfs_wall_unshaded_addresses;fn.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
for batch in batches(trace):
 key=(batch['begin_refresh'],batch['end_refresh'])
 if key not in poses:continue
 corners=poses[key]['native_corners'];points=[list(p)+list(uv) for p,uv in zip(corners,[(0,0),(2,0),(2,1),(0,1)])];counts=collections.Counter();samples=[];active=None;columns=0
 def sample(x,y):
  for ids in ((0,1,2),(0,2,3)):
   a,b,c=[points[i] for i in ids];den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1]);assert abs(den)>1e-9
   wa=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den;wb=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;wc=1-wa-wb
   if min(wa,wb,wc)<0:continue
   q=wa/a[2]+wb/b[2]+wc/c[2];return [sum(w*t[k]/t[2] for w,t in zip((wa,wb,wc),(a,b,c)))/q for k in (3,4)]
  return None
 for e in batch['events']:
  if e['pc'] in (0x030032f0,0x03004770):active=None
  if e['pc']==0x03000304:
   active=e['blocks'][5][0]
   if active==0x08574c3c:texture=e['blocks'][66][1];texture_base=e['blocks'][66][0]
  if active!=0x08574c3c or e['pc']!=0x030053e8:continue
  state=e['blocks'][75][1];words=struct.unpack('<17I',state);assert words[9]==texture_base and not(words[6] and words[11]>0x1b000);columns+=1
  n=e['regs'][3];src=(C.c_uint*320)();dst=(C.c_uint*320)();assert fn(C.create_string_buffer(state),e['regs'][1],e['regs'][2],n,src,dst)
  for a,b in zip(list(src)[:n],list(dst)[:n]):
   original_offset=a-texture_base;assert 0<=original_offset<len(texture);original=texture[original_offset];page=0x0600a000 if b>=0x0600a000 else 0x06000000;logical=b-page;y,x=divmod(logical,240);assert 0<=y<160 and x%2==0
   for pair in (0,1):
    counts['pair_samples']+=1;uv=sample(x+pair+.5,y+.5)
    if uv is None:counts['outside_geometry']+=1;counts['outside_geometry_nonzero']+=bool(original);continue
    counts['inside_geometry']+=1;tx=math.floor(uv[0]*64)%64;ty=math.floor(uv[1]*64)%64;native=texture[ty*64+tx];counts['same_address' if ty*64+tx==original_offset else 'different_address']+=1;counts['same_index' if native==original else 'different_index']+=1;counts['same_zero' if bool(native)==bool(original) else 'different_zero']+=1
    counts['same_vertical_row' if ty==original_offset//64 else 'different_vertical_row']+=1
    if bool(native)!=bool(original):counts['zero_difference_same_row' if ty==original_offset//64 else 'zero_difference_different_row']+=1
    if bool(native)!=bool(original) and len(samples)<16:samples.append(dict(x=x+pair,y=y,original_texel=[original_offset%64,original_offset//64],native_texel=[tx,ty],original_index=original,native_index=native))
 checks.append(dict(interval=key,columns=columns,counts=dict(counts),zero_difference_samples=samples))
assert len(checks)==6 and sum(c['columns'] for c in checks)==312 and sum(c['counts']['pair_samples'] for c in checks)==39196
summary=dict(sum((collections.Counter(c['counts']) for c in checks),collections.Counter()));out=capture_path.with_name(capture_path.stem.replace('-verification','-sign-continuous-sampling')+'.json');out.write_text(json.dumps(dict(result='COMPARED',projection_report_sha256=hashlib.sha256(Path(sys.argv[2]).read_bytes()).hexdigest(),checks=checks,summary=summary,scope='Actual original source texel addresses and paired-pixel centers versus perspective-correct sampling of verified recovered continuous world corners. CPU reference only, not exact GPU interpolation/readback, whole-scene fidelity or motion. Outside-geometry terminal samples retained in measurements; no geometry quantization or asset reduction.'),indent=2));print(json.dumps(summary))
