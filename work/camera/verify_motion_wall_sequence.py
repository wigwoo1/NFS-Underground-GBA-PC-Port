from pathlib import Path
import ctypes as C,json,struct
from scene_batches import records
from wall_native_prepared import prepared_edge
p=Path('work/camera');events={e['id']:e for e in records(p/'motion-original-source-8750-8781.bin')}
table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());f=C.CDLL(str((p/'native_wall.dll').resolve())).nfs_wall_default_plan;f.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint32,C.c_void_p,C.c_void_p]
native=[];draws=[]
for scene in json.loads((p/'motion-wall-snapshots.json').read_text())['scenes']:
 for wall in scene['walls']:
  event=events[wall['event']];fb=struct.unpack_from('<I',event['blocks'][3][1])[0];out=(C.c_uint32*720)();count=C.c_uint()
  assert f(prepared_edge(wall,table),table,(C.c_uint*4)(*wall['bounds']),fb,out,C.byref(count))
  start=len(native)
  native.extend([list(out[i*6:i*6+6]) for i in range(count.value)])
  draws.append(dict(event=wall['event'],start=start,count=count.value))
original=[];states=[];refresh=[];raw=(p/'motion-original-span-hooks.bin').read_bytes()
for off in range(0,len(raw),140):
 w=struct.unpack_from('<35I',raw,off)
 if w[1]!=0x030053e8:continue
 regs=w[2:18];state=w[18:]
 states.append(state);original.append([state[1],state[13],state[11],regs[1],regs[2],regs[3]]);refresh.append(w[0])
starts=[i for i in range(len(original)-len(native)+1) if original[i:i+len(native)]==native]
material_checks=[]
if len(starts)==1:
 for draw in draws:
  event=events[draw['event']];mat=event['blocks'][8][1];descriptor=event['blocks'][4][1];fb=event['blocks'][3][1]
  shift,height=struct.unpack_from('<2H',mat,36)
  expected={2:struct.unpack_from('<I',fb,12)[0]>>1,3:shift,4:height,6:((struct.unpack_from('<H',descriptor,2)[0]>>4)^1)&1,7:height<<shift,9:struct.unpack_from('<I',mat,40)[0],16:(1<<(shift+15))-1}
  for i in range(draw['count']):
   state=states[starts[0]+draw['start']+i]
   material_checks.append(all(state[k]==v for k,v in expected.items()))
report=dict(result='PASS_CAPTURED_WALL_SEQUENCE' if len(starts)==1 and all(material_checks) else 'WALL_SEQUENCE_DIFFERENCE',native_columns=len(native),material_state_columns_exact=sum(material_checks),material_state_columns_checked=len(material_checks),captured_columns=len(original),exact_contiguous_start_candidates=starts,draws=draws,scope='Ordered six-field wall column signatures from native world/source prepared edges and captured material/bounds vs actual original writer capture. Capture prefix/suffix outside seven complete scenes excluded. No palette/fullscene/timing proof.')
(p/'motion-wall-sequence-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(p/'native-wall-writer-calls.json').write_text(json.dumps(dict(draws=draws,columns=native),indent=2),encoding='utf-8')
print({k:v for k,v in report.items() if k not in ('draws','scope')})
