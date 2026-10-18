"""Split existing consumer timer without changing native draw or copy order."""
from owned_uncovered_window_candidate import OwnedD3DConsumer
import os
import owned_ordered_render_tail_install_candidate as ordered
source=ordered.source
needle='  nv,nd,overflow,nt,nb=stats;'
assert source.count(needle)==1
source=source.replace(needle,"  stage('source_bundle_copy')\n"+needle)
needle='  assert profiled(self,"nf_d3d_material_packet_cached",'
assert source.count(needle)==1
source=source.replace(needle,"  stage('vertices_copy_convert')\n"+needle)
source=source.replace("stage('material_copy_upload')","stage('material_cached_upload')")
cpu_profile=os.environ.get('NFSUG_CONSUMER_CPU_PROFILE')=='1'
if cpu_profile:
 clear_needle="  assert d.nf_d3d_clear(F32_4(.035,.05,.08,1))==0"
 assert source.count(clear_needle)==1
 clear_replacement="  clear_color=(C.c_float*4)(.035,.05,.08,1);clear_begin=time.perf_counter_ns();clear_cycles_begin=owned_thread_cycles.read();clear_result=d.nf_d3d_clear(clear_color);clear_end=time.perf_counter_ns();clear_cycles_end=owned_thread_cycles.read();self.d3d_call_profiles.append(dict(call='nf_d3d_clear',caller_begin_ns=clear_begin,caller_end_ns=clear_end,native_begin_ns=clear_begin,native_end_ns=clear_end,native_cycles=clear_cycles_end-clear_cycles_begin));assert clear_result==0"
 source=source.replace(clear_needle,clear_replacement)
if cpu_profile:
 import owned_thread_cycles
 needle='ticks=[time.perf_counter_ns()];self.stage_profile=[]'
 assert source.count(needle)==1
 source=source.replace(needle,'ticks=[time.perf_counter_ns()];stage_cpu_ticks=[owned_thread_cycles.read()];self.stage_profile=[]')
 needle='now=time.perf_counter_ns();self.stage_profile.append(dict(stage=name,elapsed_ns=now-ticks[-1]));ticks.append(now)'
 assert source.count(needle)==1
 source=source.replace(needle,'now=time.perf_counter_ns();cycles=owned_thread_cycles.read();self.stage_profile.append(dict(stage=name,elapsed_ns=now-ticks[-1],thread_cycles=cycles-stage_cpu_ticks[-1]));ticks.append(now);stage_cpu_ticks.append(cycles)')
ns=dict(OwnedD3DConsumer.render.__globals__)
if cpu_profile:ns['owned_thread_cycles']=owned_thread_cycles
exec(compile(source,'current-consumer-copy-stage-split','exec'),ns)
OwnedD3DConsumer.render=ns['render']
