import runpy
from pathlib import Path
original=Path.read_text;target=Path('work/camera/run_queued_source_anchor_candidate.py').resolve()
def read(path,*args,**kwargs):
 s=original(path,*args,**kwargs)
 if path.resolve()==target:
  assert s.count('owned-sky-source-context-candidate.dll')==1;s=s.replace('owned-sky-source-context-candidate.dll','owned-gpu-playable-input-profile-candidate.dll')
  marker=" path=Path('work/camera/prototype-runs')";assert s.count(marker)==1
  export=" gpu.nf_hud_cpu_profile_count.restype=C.c_uint;gpu.nf_hud_cpu_profile_read.argtypes=[C.c_void_p,C.c_uint];count=gpu.nf_hud_cpu_profile_count();cpurows=(C.c_uint64*(count*11))();assert gpu.nf_hud_cpu_profile_read(cpurows,count);hud_cpu_profile=dict(columns=['epoch','refresh','reuse','has_text','lookup_wall_ns','lookup_cycles','prepare_wall_ns','prepare_cycles','prepare_thread_100ns','candidate_builds','ok'],records=[list(cpurows[i*11:(i+1)*11]) for i in range(count)],dropped=gpu.nf_hud_cpu_profile_dropped())\n"
  export+=" gpu.nf_hud_input_profile_count.restype=C.c_uint;gpu.nf_hud_input_profile_read.argtypes=[C.c_void_p,C.c_uint];n=gpu.nf_hud_input_profile_count();rows=(C.c_uint64*(n*7))();assert gpu.nf_hud_input_profile_read(rows,n);hud_input_profile=dict(records=[list(rows[i*7:(i+1)*7]) for i in range(n)],dropped=gpu.nf_hud_input_profile_dropped())\n"
  s=s.replace(marker,export+marker).replace('dict(targets=list(targets),fences=list(fences))','dict(targets=list(targets),fences=list(fences),hud_cpu_profile=hud_cpu_profile,hud_input_profile=hud_input_profile)')
 return s
Path.read_text=read
runpy.run_path('work/camera/run_source_compact_single_candidate.py',run_name='__main__')


