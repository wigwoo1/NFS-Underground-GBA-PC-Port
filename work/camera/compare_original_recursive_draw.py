"""Native command planner versus captured recursive original diagnostic."""
from pathlib import Path
import ctypes as C,struct,json,os
p=Path(__file__).resolve().parent;raw=(p/os.environ.get('NF_ORACLE_FIXTURE','arm-oracle-fresh-16-17-50-after.bin')).read_bytes();rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();original=json.loads((p/'original-road-write-diagnostic.json').read_text());P=C.c_void_p;U=C.c_uint32
Read=C.CFUNCTYPE(C.c_int,P,U,P,C.c_size_t);Callback=C.CFUNCTYPE(C.c_int,P,C.c_uint,C.c_uint,P,C.c_uint,P,P,P,P)
class Command(C.Structure):
 _fields_=[('head',U*13),('record',C.c_uint8*16),('state',C.c_uint8*256),('model',C.c_uint8*68),('billboard',U*18),('vertex_count',U),('edge',C.c_uint8*52),('vertices',C.c_int32*(128*6)),('bounds',C.c_uint16*4),('cell_end',U)]
def memory(a,n):
 for base,data in [(0x02000000,raw[:0x40000]),(0x03000000,raw[0x40000:]),(0x08000000,rom)]:
  if base<=a and a+n<=base+len(data):return data[a-base:a-base+n]
 raise ValueError(hex(a))
state=memory(0x030000c0,256);queue,groups=struct.unpack_from('<2I',state,96);pool=struct.unpack_from('<I',state,60)[0];matrix=struct.unpack_from('<I',state,84)[0];objects=C.create_string_buffer(memory(pool,256*164),256*164);current_objects=None
@Read
def read(ctx,a,out,n):
 try:
  data=C.string_at(current_objects+a-pool,n) if current_objects and pool<=a and a+n<=pool+256*164 else memory(a,n);C.memmove(out,data,n);return 1
 except:return 0
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_object_callback12_owned.argtypes=[P,P,P,P,Read,P,P];d.nf_scene_command_plan.argtypes=[P,P,C.c_uint,P,C.c_uint,P,Read,P,P,Callback,P,P,C.c_uint,P];counter=U(struct.unpack('<I',memory(0x03005ac8,4))[0]);scratch=C.create_string_buffer(3072);calls=[]
@Callback
def callback(ctx,index,selector,obj,count,bits,mat,head,maximum):
 global current_objects
 calls.append([index,selector]);current_objects=obj
 if selector!=12:return 0
 event=U();return d.nf_object_callback12_owned(C.create_string_buffer(state,256),obj+index*164,C.byref(counter),scratch,read,None,C.byref(event))
commands=(Command*144)();count=U();bits=C.create_string_buffer(32);reciprocal=C.create_string_buffer(rom[0x627700:0x647700]);ok=d.nf_scene_command_plan(C.create_string_buffer(state,256),C.create_string_buffer(memory(queue,512),512),struct.unpack_from('<H',state,238)[0],objects,256,bits,read,None,reciprocal,callback,None,commands,144,C.byref(count));detail=(U*18)();d.nf_scene_command_plan_detail(detail)
native=[dict(kind=c.head[0],source=c.head[5],material=c.head[9],material_bytes=memory(c.head[9],32).hex(),resolved=[struct.unpack_from('<I',bytes(c.state),80)[0],c.head[11],c.head[12],c.head[10]],bounds=list(c.bounds),record=bytes(c.record).hex(),pass_value=c.head[2]) for c in commands[:count.value] if c.head[0] in (1,2)]
d.nf_road_span_plan.argtypes=[P,C.c_uint,C.c_int32,C.c_int32,C.c_uint,C.c_uint,P,P,P,C.c_uint,P]
world_commands=[c for c in commands[:count.value] if c.head[0] in (1,2)]
for i,c in enumerate(world_commands):
 if c.head[0]==1:
  spans=(U*(512*4))();amount=U();fb=C.create_string_buffer(memory(struct.unpack_from('<I',bytes(c.state),80)[0],16),16);inherited=original['events'][i]['bounds'];assert d.nf_road_span_plan(c.vertices,c.vertex_count,inherited[2],inherited[3],c.head[6],c.head[7],reciprocal,fb,spans,512,C.byref(amount));native[i]['spans']=[list(spans[k*4:k*4+4]) for k in range(amount.value)]
expected=[dict(kind=2 if e['pc']=='0x3000304' else 1,source=e['registers'][6] if e['pc']=='0x3000304' else e['registers'][7],material=e['material'],material_bytes=e['material_bytes'],resolved=[struct.unpack_from('<I',bytes.fromhex(e['material_bytes']),8)[0],*struct.unpack_from('<2H',bytes.fromhex(e['material_bytes']),36),struct.unpack_from('<I',bytes.fromhex(e['material_bytes']),40)[0]],record=e['record'],pass_value=e['pass_value'],bounds=e['bounds']) for e in original['events']]
for e,draw in zip(expected,original['events']):
 if draw['pc']=='0x30032f0' and draw.get('write_max') is not None:e['bounds'][3]=max(e['bounds'][3],min(160,(draw['write_max']-0x06000000+239)//240))
for i,c in enumerate(world_commands):
 if c.head[0]==2:
  native[i]['wall_descriptor']=memory(c.head[9],48).hex();native[i]['wall_flags']=c.head[6];expected[i]['wall_descriptor']=original['events'][i]['wall_descriptor'];expected[i]['wall_flags']=original['events'][i]['wall_flags']
comparisons=[dict(index=i,source_exact=n['kind']==e['kind'] and n['source']==e['source'],bounds_exact=n['bounds']==e['bounds'],material_exact=n['resolved']==e['resolved'],wall_inputs_exact=n['kind']!=2 or (n['material']==original['events'][i]['registers'][3] and n['wall_descriptor']==e['wall_descriptor'] and n['wall_flags']==e['wall_flags']),record_exact=n['record']==e['record'],pass_exact=n['pass_value']==e['pass_value']) for i,(n,e) in enumerate(zip(native,expected))]
report=dict(result='COMPARISON_DIAGNOSTIC',native_ok=bool(ok),detail=list(detail),callbacks=calls,native=native,original=expected,comparisons=comparisons,scope='One coherent midpoint; original raster bypass/dummy peripheral memory; no broad fidelity or gameplay proof.')
(p/'recursive-original-native-comparison.json').write_text(json.dumps(report,indent=2));print('native',ok,'commands',count.value,'world',len(native),'original',len(expected),'source exact',sum(c['source_exact'] for c in comparisons),'bounds exact',sum(c['bounds_exact'] for c in comparisons),'detail',list(detail)[:5])






