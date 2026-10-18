import ctypes as C,json
from pathlib import Path
from owned_ordered_render_tail_binding_candidate import Tail,bridge,address,P,Z,U
Sky=C.CFUNCTYPE(C.c_int,P,P);World=C.CFUNCTYPE(C.c_int,P,U,Z,P,Z,P,Z,P,U,Z);Hud=C.CFUNCTYPE(C.c_int,P,P,P,P)
log=[];failure=0
@Sky
def sky(a,b):log.append(1);return 71 if failure==1 else 0
@World
def world(v,n,vb,o,ob,i,ib,s,nd,sb):log.append(2);assert (n,vb,ob,ib,nd,sb)==(6,240,8,4,1,72);return 72 if failure==2 else 0
@Hud
def hud(a,b,c,d):log.append(3);return 73 if failure==3 else 0
job=Tail(*[address(sky),address(world),address(hud)]+[1]*7,6,240,1,8,1,4,1,1,72)
for failure in (0,1,2,3):
 log.clear();stage=U(99);status=bridge.nf_ordered_render_tail(C.byref(job),C.sizeof(job),C.byref(stage));assert log==([1,2,3] if failure==0 else list(range(1,failure+1))) and stage.value==failure and status==(0 if failure==0 else 70+failure)
log.clear();job.vb=239;stage=U(99);assert bridge.nf_ordered_render_tail(C.byref(job),C.sizeof(job),C.byref(stage))==37 and log==[] and stage.value==99
Path('work/camera/prototype-runs/ordered-tail-component-20261009.json').write_text(json.dumps(dict(result='PASS_ORDERED_TAIL_COMPONENT',scope='Mocknativecallorder/argumentforwarding/failstop/prevalidation; noactualgraphicsor60fps proof.'),indent=2));print('PASS_ORDERED_TAIL_COMPONENT')
