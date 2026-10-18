from pathlib import Path
import json,struct,ctypes as C
from scene_batches import records
p=Path('work/camera');events=list(records(p/'motion-original-source-8750-8781.bin'));table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());source=C.CDLL(str((p/'road-source-ring-motion-audit.dll').resolve())).nf_road_source_ring;source.argtypes=[C.c_void_p,C.c_uint]+[C.c_void_p]*5+[C.c_uint,C.c_void_p];clip=C.CDLL(str((p/'road-clip-continuous.dll').resolve())).nf_road_clip_continuous;clip.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];scratch={};checks=[]
i=lambda b,o:struct.unpack_from('<i',b,o)[0];h=lambda b,o:struct.unpack_from('<h',b,o)[0]
for draw in events:
 if draw['pc']!=0x030032f0:continue
 blocks={k:v[1] for k,v in draw['blocks'].items()};descriptor=draw['blocks'][4][0]
 before=max((e for e in events if e['id']<draw['id'] and e['pc']==0x03001800 and e['blocks'][4][0]==descriptor),key=lambda e:e['id']);after=min((e for e in events if before['id']<e['id']<draw['id'] and e['pc']==0x03002964 and e['blocks'][4][0]==descriptor),key=lambda e:e['id'])
 count=struct.unpack_from('<H',blocks[4],2)[0];face=blocks[42] or bytes(20);world=[];attrs=[]
 for j in range(count):
  v=blocks[5][j*68:(j+1)*68];off=blocks[10+j] or bytes(32);world.extend([i(v,0)+h(off,0),h(v,56)+h(off,6)+h(face,6),i(v,4)+h(off,2)]);attrs.extend([i(v,32),i(v,36)])
 shift,height=struct.unpack_from('<2H',blocks[8],36);affine=struct.unpack('<2I',blocks[69])[0];header=[count,shift,height,affine,0,0,0,0];raw=struct.pack('<6I66i',*header,*attrs,*([0]*(64-count*2)));out=(C.c_double*320)();n=C.c_uint();assert source((C.c_double*len(world))(*world),count,raw,blocks[2],(C.c_int32*3)(120,87,128),table,out,64,C.byref(n));base=before['blocks'][7][0];ring=[];missing=[]
 for j in range(n.value):
  x,y,q,u,v=out[j*5:j*5+5];address=base+j*24+12
  if affine:
   if address not in scratch:missing.append(j)
   q=scratch.get(address,0)
  else:scratch[address]=q
  ring.append([x,y,y,q,u,v])
 original_n=struct.unpack_from('<H',after['blocks'][1][1],242)[0];expected=[[i(after['blocks'][7][1],j*24+k) for k in (0,4,12,16,20)] for j in range(original_n)];actual=[[v[k] for k in (0,1,3,4,5)] for v in ring];bd=struct.unpack_from('<4H',blocks[1],226);first,expected_count=struct.unpack_from('<2H',blocks[1],242);clipped=(C.c_double*768)();cn=C.c_uint();assert clip((C.c_double*(len(ring)*6))(*(v for row in ring for v in row)),len(ring),bd[0],bd[1],table,clipped,128,C.byref(cn))
 for j in range(cn.value):scratch[base+(first+j)*24+12]=clipped[j*6+3]
 clip_expected=[[i(blocks[7],(first+j)*24+k) for k in (0,4,12,16,20)] for j in range(expected_count)];clip_actual=[[clipped[j*6+k] for k in (0,1,3,4,5)] for j in range(cn.value)]
 checks.append(dict(clipped_ring=[list(clipped[j*6:j*6+6]) for j in range(cn.value)],bounds=list(bd),orientation=struct.unpack('<2I',blocks[69])[1],framebuffer=struct.unpack_from('<I',blocks[3])[0],material_hex=blocks[8].hex(),offsets=list(struct.unpack_from('<2h',blocks[9],4)),clipped_fields_exact=clip_actual==clip_expected,event=draw['id'],refresh=draw['frame'],source=descriptor,affine=affine,missing_initial_slots=missing,source_exact=actual==expected,clip_count_exact=cn.value==expected_count,first=first,emitted=n.value))
r=dict(result='PASS_NATIVE_SCRATCH_REPLAY' if all(v['source_exact'] and v['clip_count_exact'] and not v['missing_initial_slots'] for v in checks) else 'NATIVE_SCRATCH_REPLAY_DIFFERENCE',checks=checks,scope='Native world emitter and clipped Q writes in captured road draworder; no captured projected valuesseed scratch. Initial capture state missing slots explicit; scheduler/material/fullscene verification pending.')
r['post_warmup_draws']=len(checks)-2;r['post_warmup_exact']=all(v['source_exact'] and v['clipped_fields_exact'] and not v['missing_initial_slots'] for v in checks[2:]);r['initial_unresolved_draws']=checks[:2]
(p/'native-road-scratch-replay.json').write_text(json.dumps(r,indent=2));print(r['result'],len(checks));print([v for v in checks if not v['source_exact'] or not v['clip_count_exact'] or v['missing_initial_slots']])
