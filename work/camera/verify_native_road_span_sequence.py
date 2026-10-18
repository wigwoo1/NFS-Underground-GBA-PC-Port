from pathlib import Path
import ctypes as C,json,struct,csv
p=Path('work/camera');d=C.CDLL(str((p/'road-polygon-clip.dll').resolve()));plan=d.nf_road_span_contexts;plan.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_int,C.c_uint,C.c_uint]+[C.c_void_p]*4+[C.c_uint,C.c_void_p];perspective=d.nf_road_perspective_plan;perspective.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());generated=[];draws=[];fields=(0,1,2,5,6,7,8,9,10,11,14,15)
for road in json.loads((p/'native-road-scratch-replay.json').read_text())['checks'][2:]:
 ring=road['clipped_ring'];material=bytes.fromhex(road['material_hex']);shift,height=struct.unpack_from('<2H',material,36);seed=[0]*16;seed[0]=shift;seed[1]=(1<<(shift+15))-1;seed[2]=(height<<15)-1;seed[5]=struct.unpack_from('<I',material,40)[0];seed[14]=(road['offsets'][0]<<7)&0xffffffff;seed[15]=(road['offsets'][1]<<7)&0xffffffff
 out=(C.c_uint32*(512*20))();n=C.c_uint();bd=road['bounds'];assert plan((C.c_int32*(len(ring)*6))(*(int(v) for row in ring for v in row)),len(ring),bd[2],bd[3],road['orientation'],road['affine'],table,(C.c_uint32*4)(road['framebuffer'],0,0,240),(C.c_uint32*16)(*seed),out,512,C.byref(n))
 start=len(generated)
 for j in range(n.value):
  span=list(out[j*20:j*20+20]);params=span[4:];runs=[params]
  if span[2]==0x03003190:
   buf=(C.c_uint32*512)();count=C.c_uint();final=(C.c_uint32*16)();assert perspective((C.c_uint32*16)(*params),table,buf,32,C.byref(count),final);runs=[list(buf[k*16:k*16+16]) for k in range(count.value)]
  generated.extend(dict(refresh=road['refresh'],event=road['event'],params=r,signature=[r[k] for k in fields]+[span[3]]) for r in runs)
 draws.append(dict(event=road['event'],affine=road['affine'],native_spans=n.value,writer_calls=len(generated)-start))
raw=(p/'motion-original-span-hooks.bin').read_bytes();rows=[struct.unpack_from('<35I',raw,j) for j in range(0,len(raw),140)];writers=[r for r in rows if r[1]==0x030056d8];cycles=list(csv.DictReader((p/'motion-original-span-cycles.csv').open()));assert len(writers)==len(cycles);original=[dict(refresh=r[0],signature=[r[18+k] for k in fields]+[int(c['double'])]) for r,c in zip(writers,cycles)]
starts=[i for i,r in enumerate(original) if r['signature']==generated[0]['signature']];checks=[]
for start in starts:
 tail=original[start:];mismatch=next((i for i,(a,b) in enumerate(zip(generated,tail)) if a['signature']!=b['signature']),None);checks.append(dict(refresh_crossings=sum(a['refresh']!=b['refresh'] for a,b in zip(generated,tail)),original_start=start,native_calls=len(generated),original_remaining=len(tail),first_mismatch=mismatch,exact=mismatch is None and len(tail)==len(generated),difference=None if mismatch is None else dict(native=generated[mismatch],original=tail[mismatch])))
r=dict(result='PASS_ROAD_WRITER_SEQUENCE' if any(v['exact'] for v in checks) else 'ROAD_WRITER_SEQUENCE_DIFFERENCE',fields=list(fields),draws=draws,alignment_checks=checks,scope='Ordered native writer-used fields and doubledflag vs originalcalls aftertwo initial unresolveddraws. Non-writer metadata omitted; source/clippedgeometry reconstructednative. Drawentry refresh and perwriter refresh may differ when originalCPU crosses VBlank mid-draw; refresh mismatches reported separately, no timing proof. No texturepixels/fullscene gameplay proof.')
(p/'native-road-writer-calls.json').write_text(json.dumps(generated))
(p/'native-road-span-sequence-tests.json').write_text(json.dumps(r,indent=2));print(r['result'],len(generated),len(original));print(checks[:2])
