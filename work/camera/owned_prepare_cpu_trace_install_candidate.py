"""Experimental renderer-thread CPU versus wall-time stage accounting."""
import ast,inspect,textwrap,time
from pathlib import Path
from owned_thread_cycles import read as thread_cycles
from owned_uncovered_window_candidate import OwnedD3DConsumer
import owned_native_source_hud_cache_lease_session_candidate as hud
from owned_renderer_fixed_types_install_candidate import U32_3,U32_2,F32_4

def install_render():
 source=Path(__file__).with_name('owned_source_d3d_sky_pan_candidate.py').read_text()
 tree=ast.parse(source);cls=next(x for x in tree.body if isinstance(x,ast.ClassDef));method=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='render')
 source=textwrap.dedent(ast.get_source_segment(source,method))
 source=source.replace('ticks=[time.perf_counter_ns()];self.stage_profile=[]','ticks=[time.perf_counter_ns()];cpu_ticks=[time.thread_time_ns()];cycle_ticks=[thread_cycles()];self.stage_profile=[]')
 old="now=time.perf_counter_ns();self.stage_profile.append(dict(stage=name,elapsed_ns=now-ticks[-1]));ticks.append(now)"
 assert source.count(old)==1
 source=source.replace(old,"now=time.perf_counter_ns();cpu_now=time.thread_time_ns();cycle_now=thread_cycles();self.stage_profile.append(dict(stage=name,elapsed_ns=now-ticks[-1],thread_cycles=cycle_now-cycle_ticks[-1],thread_cpu_ns=cpu_now-cpu_ticks[-1]));ticks.append(now);cpu_ticks.append(cpu_now);cycle_ticks.append(cycle_now)")
 for old,new in [('(C.c_uint*3)()','U32_3()'),('(C.c_uint*2)()','U32_2()'),('(C.c_float*4)(.035,.05,.08,1)','F32_4(.035,.05,.08,1)')]:
  assert old in source;source=source.replace(old,new)
 ns=dict(OwnedD3DConsumer.render.__globals__);ns.update(U32_3=U32_3,U32_2=U32_2,F32_4=F32_4,thread_cycles=thread_cycles)
 exec(compile(source,'prepare-cpu-render','exec'),ns);OwnedD3DConsumer.render=ns['render']

def install_prepare():
 method=hud.NativeSourceSession.prepare;source=textwrap.dedent(inspect.getsource(method))
 for old,new in [('source_begin=time.perf_counter_ns();hud_profile=None','source_begin=time.perf_counter_ns();source_cpu_begin=time.thread_time_ns();source_cycle_begin=thread_cycles();hud_profile=None'),('snapshot_begin=time.perf_counter_ns();snapshot_new','snapshot_begin=time.perf_counter_ns();snapshot_cpu_begin=time.thread_time_ns();snapshot_cycle_begin=thread_cycles();snapshot_new'),('snapshot_end=time.perf_counter_ns()','snapshot_end=time.perf_counter_ns();snapshot_cpu_end=time.thread_time_ns();snapshot_cycle_end=thread_cycles()'),('source_end=time.perf_counter_ns()','source_end=time.perf_counter_ns();source_cpu_end=time.thread_time_ns();source_cycle_end=thread_cycles()'),('snapshot_new=snapshot_new,snapshot_begin_ns=','snapshot_thread_cycles=snapshot_cycle_end-snapshot_cycle_begin,snapshot_thread_cpu_ns=snapshot_cpu_end-snapshot_cpu_begin,snapshot_new=snapshot_new,snapshot_begin_ns='),('source_prepare_ns=source_end-source_begin,','source_prepare_ns=source_end-source_begin,source_prepare_thread_cycles=source_cycle_end-source_cycle_begin,source_prepare_thread_cpu_ns=source_cpu_end-source_cpu_begin,')]:
  assert source.count(old)==1,old;source=source.replace(old,new)
 ns=dict(method.__globals__);ns.update(thread_cycles=thread_cycles);exec(compile(source,'prepare-cpu-session','exec'),ns);hud.NativeSourceSession.prepare=ns['prepare']
install_render();install_prepare()
