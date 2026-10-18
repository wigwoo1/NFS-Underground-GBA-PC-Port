"""Compile actual pose/capture helpers; test camera removal and provenance guards."""
from pathlib import Path
import ctypes as C,hashlib,json,math,os,random,struct,subprocess
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');core=base/'NFSUG-pc-traffic-rotation-core';out=base/'NFSUG-pc-traffic-rotation-helper-tests';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();build=json.loads((core/'traffic-rotation-build-report.json').read_text())
for n in ['traffic_rotation_pose.inc','traffic_rotation_capture.inc']:assert sha(here/n)==build['maintained_source_sha256'][n]
code=r'''
#include <stdint.h>
#include <string.h>
struct ARMCore {int32_t gprs[16];};
static unsigned frame_value=100;
static unsigned frame_counter(void*unused){(void)unused;return frame_value;}
static struct {unsigned(*frameCounter)(void*);} fake_core={frame_counter};
static void* unused_core;
#define c (&fake_core)
static uint64_t live_scene_epoch=2;
static struct {unsigned serial,slot;struct {unsigned address,frame;int32_t matrix[12];unsigned traffic,traffic_object,traffic_camera,traffic_serial;uint64_t traffic_epoch;int32_t traffic_cm[12],traffic_actual[9];}rotations[16];}live_scene;
static uint8_t ram[4096];
static int native_surface_read(void*u,uint32_t a,void*out,size_t n){(void)u;if(a<0x02000000||(uint64_t)a+n>0x02001000)return 0;memcpy(out,ram+a-0x02000000,n);return 1;}
#include "traffic_rotation_capture.inc"
__declspec(dllexport) int recover(const int32_t*cma,const int32_t*a,const int32_t*b,const int32_t*m,int32_t*out){return nf_traffic_rotation_pose(cma,a,b,m,out);}
#define CHECK(x) do{if(!(x))return __LINE__;}while(0)
static void begin(struct ARMCore*cpu){memset(cpu,0,sizeof(*cpu));cpu->gprs[0]=0x02000100;cpu->gprs[1]=0x02000200;cpu->gprs[2]=0x02000400;nf_traffic_event(cpu,0x08022c24);}
__declspec(dllexport) int guards(void){
 (void)unused_core;struct ARMCore cpu;int32_t id[12]={16384,0,0,0,16384,0,0,0,16384,0,0,0};
 memset(&live_scene,0,sizeof(live_scene));memset(ram,0,sizeof(ram));live_scene.serial=9;nf_traffic_reset();memcpy(ram+0x100,id,48);memcpy(ram+0x600,id,48);memcpy(ram+0x700,id,48);
 begin(&cpu);CHECK(nf_traffic_pending.active);cpu.gprs[1]=0x02000600;cpu.gprs[2]=0x02000100;cpu.gprs[3]=0x02000500;nf_traffic_event(&cpu,0x08022d38);CHECK(nf_traffic_pending.phase==1);
 memcpy(ram+0x500,id,36);cpu.gprs[1]=0x02000500;cpu.gprs[2]=0x02000700;cpu.gprs[3]=0x02000400;nf_traffic_event(&cpu,0x08022d44);CHECK(nf_traffic_pending.phase==2);
 memcpy(ram+0x400,id,36);cpu.gprs[8]=0x02000400;nf_traffic_event(&cpu,0x08022d48);CHECK(nf_traffic_stats[1]==1&&live_scene.rotations[0].traffic);CHECK(nf_traffic_rotation_valid(0,0x02000100,0x02000200));
 CHECK(!nf_traffic_rotation_valid(0,0x02000100,0x02000204));CHECK(!nf_traffic_rotation_valid(0,0x02000104,0x02000200));
 ram[0x100]^=1;CHECK(!nf_traffic_rotation_valid(0,0x02000100,0x02000200));ram[0x100]^=1;
 ram[0x400]^=1;CHECK(!nf_traffic_rotation_valid(0,0x02000100,0x02000200));ram[0x400]^=1;
 live_scene_epoch++;CHECK(!nf_traffic_rotation_valid(0,0x02000100,0x02000200));live_scene_epoch--;
 live_scene.serial++;CHECK(!nf_traffic_rotation_valid(0,0x02000100,0x02000200));live_scene.serial--;
 begin(&cpu);frame_value++;nf_traffic_event(&cpu,0x08022d38);CHECK(!nf_traffic_pending.active);frame_value--;
 begin(&cpu);cpu.gprs[1]=0x02000600;cpu.gprs[2]=0x02000104;cpu.gprs[3]=0x02000500;nf_traffic_event(&cpu,0x08022d38);CHECK(!nf_traffic_pending.active);
 nf_traffic_reset();CHECK(!nf_traffic_pending.active);return 0;
}
'''
(out/'test.c').write_text(code);staged=core/'source';dll=out/'helper.dll';cmd=['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O2','-Wall','-Wextra','-Werror','-shared','-I'+str(staged),'-I'+str(staged/'camera'),str(out/'test.c'),str(staged/'camera/rigid_motion.c'),'-lm','-o',str(dll)]
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(cmd,env=env,check=True,capture_output=True)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(dll))
P=C.c_void_p;d.recover.argtypes=[P]*5;d.guards.restype=C.c_int;assert d.guards()==0
A=C.c_int32*12
signed=lambda w:list(struct.unpack('<%di'%len(w),struct.pack('<%dI'%len(w),*w)))
trace=json.loads((base/'NFSUG-pc-rotation-trace-v4-core/probe/rotation-events.json').read_text());rs=[r for r in trace['records'] if r[2]==848];first=next(r for r in rs if r[3]==8);second=next(r for r in rs if r[3]==9);consumer=next(r for r in rs if r[3]==4)
real=[A(*signed(w)) for w in [first[44:56],first[32:44],second[44:56],consumer[110:122]]];outmatrix=A();assert d.recover(*real,outmatrix) and list(outmatrix)==[16384,0,0,0,16384,0,0,0,16384,0,0,0]
rng=random.Random(0x22d44)
def rotation():
 q=[rng.gauss(0,1) for _ in range(4)];n=math.sqrt(sum(x*x for x in q));x,y,z,w=[v/n for v in q]
 return [round(v*16384) for v in [1-2*(y*y+z*z),2*(x*y+z*w),2*(x*z-y*w),2*(x*y-z*w),1-2*(x*x+z*z),2*(y*z+x*w),2*(x*z+y*w),2*(y*z-x*w),1-2*(x*x+y*y)]]+[0]*3
# Original ARM multiply oracle: wrap each MLA to signed32 before arithmetic shift.
def mul(a,b):
 out=[]
 for r in range(3):
  for col in range(3):
   bits=sum(a[r*3+k]*b[k*3+col] for k in range(3))&0xffffffff
   out.append((bits if bits<0x80000000 else bits-0x100000000)>>14)
 return out+[0]*3
max_error=0
for _ in range(500):
 cm,a,b=rotation(),rotation(),rotation();actual=mul(mul(a,cm),b);result=A();assert d.recover(A(*cm),A(*a),A(*b),A(*actual),result)
 projected=mul(list(result),cm)
 # Both matrices map model axes into camera axes. Compare independent column vectors.
 error=max(abs(x-y) for x,y in zip(projected[:9],actual[:9]));max_error=max(max_error,error);assert error<=8,error
 sentinel=A(*([0x12345678]*12));bad=actual.copy();bad[0]^=1;assert not d.recover(A(*cm),A(*a),A(*b),A(*bad),sentinel) and list(sentinel)==[0x12345678]*12
zero=A();sentinel=A(*([17]*12));assert not d.recover(zero,zero,zero,zero,sentinel) and list(sentinel)==[17]*12
assert not d.recover(None,real[1],real[2],real[3],sentinel) and list(sentinel)==[17]*12
report=dict(result='PASS_GUARDED_TRAFFIC_ROTATION_HELPERS',random_nonzero_rotation_cases=500,max_q14_recomposition_error=max_error,actual_failed_vehicle_recovers_identity=True,wrong_object_camera_epoch_scene_and_mutated_matrix_rejected=True,stale_frame_and_wrong_camera_producer_rejected=True,reset_clears_pending=True,atomic_invalid_products_and_singular_and_null_rejected=True,source_sha256={n:sha(here/n) for n in ['traffic_rotation_pose.inc','traffic_rotation_capture.inc']},staged_rigid_motion_sha256=sha(staged/'camera/rigid_motion.c'),test_source_sha256=sha(out/'test.c'),script_sha256=sha(Path(__file__)),dll_sha256=sha(dll),core_build_sha256=sha(core/'traffic-rotation-build-report.json'),full_scene_60fps=False)
(out/'traffic-helper-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
