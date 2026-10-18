"""Original recovered wall draw admission for actual captured extra edges."""
import sys,ctypes as C,struct,json
from pathlib import Path
sys.path.insert(0,'work/camera');s={};exec(Path('work/camera/test_source_transition_adapter.py').read_text().split('table=struct.unpack',1)[0],s)
from owned_wall_projection import projected
from owned_closed_scene_memory import ClosedSceneMemory
closed=s['scenes'][0].graph;graph=closed.graph;table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);draws,_=projected(graph,table);memory=ClosedSceneMemory(closed,s['rom'])
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
@Reader
def read(ctx,address,dst,n):
 try:data=memory.read(address,n);C.memmove(dst,data,n);return 1
 except ValueError:return 0
fn=C.CDLL(str(Path('work/camera/native_visibility.dll').resolve())).nfs_visibility_wall_draw_plan;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint32,Reader,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
u.mem_map(0x02000000,0x40000);u.mem_map(0x03000000,0x10000);u.mem_map(0x08000000,(len(s['rom'])+4095)//4096*4096);u.mem_write(0x08000000,s['rom']);u.mem_write(0x03000000,s['rom'][0x71b0c:0x77b0c])
for address,data in memory._ranges:
 if 0x02000000<=address<0x02040000 or 0x08000000<=address<0x0a000000:u.mem_write(address,data)
arm_calls=[]
def hook(uc,pc,size,ctx):
 if pc==0x03000304:
  material=uc.reg_read(UC_ARM_REG_R0);raw=bytes(uc.mem_read(material,48));arm_calls.append([(uc.reg_read(UC_ARM_REG_R6)-0x02001000)//68,uc.reg_read(UC_ARM_REG_R3),struct.unpack_from('<I',raw,40)[0],struct.unpack_from('<H',raw,36)[0],struct.unpack_from('<H',raw,38)[0],uc.reg_read(UC_ARM_REG_R2)]);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook,begin=0x03000304,end=0x03000304)
at=0;results=[]
while at<len(graph.geometry):
 ident,count,*_=struct.unpack_from('<4I',graph.geometry,at);desc=graph.geometry[at+16:at+64];vertices=graph.geometry[at+64:at+64+count*68];at+=64+count*68
 if ident not in (34,36):continue
 selected=[x for x in draws if x[2].descriptor==ident];assert selected
 state=bytearray(graph.context[:256]);region=selected[0][1];struct.pack_into('<2H',state,0xe6,region[3],region[4]);scratch=bytearray(count*52)
 for i in range(count):struct.pack_into('<H',scratch,i*52+48,4)
 for ordinal,region,w,raw in selected:scratch[w.edge*52:(w.edge+1)*52]=raw
 out=(C.c_uint32*(32*6))();n=C.c_uint();mask=C.c_uint32()
 assert fn(C.create_string_buffer(bytes(state)),C.create_string_buffer(vertices),count,C.create_string_buffer(bytes(scratch)),0,read,None,out,32,C.byref(n),C.byref(mask))==1,(ident,memory.missing)
 arm_state=bytearray(state);struct.pack_into('<I',arm_state,16,0x02001000);struct.pack_into('<I',arm_state,104,0x02002000);arm_desc=bytearray(desc);struct.pack_into('<H',arm_desc,0,0)
 for address,data in ((0x02000000,arm_state),(0x02000100,arm_desc),(0x02001000,vertices),(0x02002000,scratch),(0x02000300,bytes(48))):u.mem_write(address,bytes(data))
 arm_calls.clear()
 for reg,value in ((UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_R1,0x02000100),(UC_ARM_REG_R2,0x02000300),(UC_ARM_REG_R3,0),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)):u.reg_write(reg,value)
 u.emu_start(0x0300264c,0x03006000,count=20000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
 assert arm_calls==[list(out[i*6:i*6+6]) for i in range(n.value)]
 results.append(dict(original_arm_calls=list(arm_calls),descriptor=ident,projection_edges=[x[2].edge for x in selected],draw_plan=[list(out[i*6:i*6+6]) for i in range(n.value)],deferred=mask.value))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-owned-draw-plan-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(dict(result='MEASURED_OWNED_DRAW_PLAN',regions=results,scope='Recovered original draw-plan helper using owned older snapshot/material memory and projected visible scratch. Rejected edges explicitly flag4. Not original ARM execution/capture-point proof.'),indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(results,indent=2))
