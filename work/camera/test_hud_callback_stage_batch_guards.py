import ctypes as C,json
from pathlib import Path
from owned_hud_callback_stage_batch_candidate import helper,P,U,S,read_stages,profile
callback_type=C.CFUNCTYPE(C.c_int,P,S,P,S,U,U);getter_type=C.CFUNCTYPE(C.c_int,C.POINTER(U))
checks=[]
for callback_result,getter_result in ((0,0),(-7,0),(0,-8),(-7,-8)):
 order=[]
 @callback_type
 def callback(ctx,prefix,tail,size,token,epoch):
  assert (ctx,prefix,tail,size,token,epoch)==(123,45,678,90,12,34);order.append('callback');return callback_result
 @getter_type
 def getter(out):
  assert order==['callback'];order.append('getter');out[0]=11;out[1]=22;out[2]=33;return getter_result
 times=(U*3)();stages=(U*3)();status=C.c_int(99)
 result=helper.nf_profile_hud_callback_stages(C.cast(callback,P),C.cast(getter,P),P(123),45,P(678),90,12,34,times,stages,C.byref(status))
 assert result==callback_result and status.value==getter_result and list(stages)==[11,22,33] and order==['callback','getter']
 assert 0<times[0]<=times[1]
 checks.append(dict(callback_result=result,getter_result=status.value))
 # Invalid wrapper arguments cannot run either callback or mutate outputs.
 for which in ('callback','getter','times','stages','status'):
  order.clear();args=[C.cast(callback,P),C.cast(getter,P),P(123),45,P(678),90,12,34,times,stages,C.byref(status)]
  args[dict(callback=0,getter=1,times=8,stages=9,status=10)[which]]=None
  assert helper.nf_profile_hud_callback_stages(*args)==-999 and order==[]
owner=object();profile.state.batched_library=owner;profile.state.batched_stage_status=0;profile.state.batched_stages=[11,22,33]
a=read_stages(owner);a[0]=99;assert read_stages(owner)==[11,22,33]
try:read_stages(object())
except RuntimeError:pass
else:raise AssertionError('Wrong stage owner accepted')
profile.state.batched_stage_status=-8
try:read_stages(owner)
except RuntimeError:pass
else:raise AssertionError('Getter failure ignored')
out=dict(result='PASS_CALLBACK_STAGE_BATCH_GUARDS',checks=checks,null_pointer_cases=20,owner_private_result_guard=True,scope='Actual native wrapper callback order/error propagation/null guards; independent of renderer pixel parity')
p=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/hud-callback-stage-batch-20261010');p.mkdir(exist_ok=True);(p/'guards.json').write_text(json.dumps(out,indent=2));print(out['result'])
