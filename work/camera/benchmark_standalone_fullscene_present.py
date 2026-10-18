import time,statistics,json,ctypes as C,struct,sys
repeat_only='--repeat-only' in sys.argv
pump_messages='--pump-messages' in sys.argv
flush_before_wait='--flush-before-wait' in sys.argv
native_draw_timing='--native-draw-timing' in sys.argv
above_normal='--above-normal-thread' in sys.argv
gpu_draw_query='--gpu-draw-query' in sys.argv
query_pending=None
frame_count=int(sys.argv[sys.argv.index('--frames')+1]) if '--frames' in sys.argv else 300
assert 2<=frame_count<=3600
from pathlib import Path
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0];exec(compile(source,'captured_full_scene_setup','exec'))
samples=[prepared.sample(i/20) for i in range(21)];gpu=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));gpu.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];gpu.nf_owned_gpu_draw_scene_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];gpu.nf_owned_gpu_present_timed.argtypes=[C.c_uint64,C.c_void_p];gpu.nf_owned_gpu_present_stages.argtypes=[C.c_void_p];gpu.nf_owned_gpu_swap_interval.argtypes=[C.c_int,C.c_void_p];rows=[]
kernel=C.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentThread.restype=C.c_void_p;kernel.GetThreadPriority.argtypes=[C.c_void_p];kernel.SetThreadPriority.argtypes=[C.c_void_p,C.c_int];thread=kernel.GetCurrentThread();prior_priority=kernel.GetThreadPriority(thread);assert prior_priority!=0x7fffffff
try:
 if above_normal:assert kernel.SetThreadPriority(thread,1)
 observed_priority=kernel.GetThreadPriority(thread)
 assert gpu.nf_owned_gpu_window(1)==0;observed=(C.c_int*2)();assert gpu.nf_owned_gpu_swap_interval(0,observed)==0
 gl=C.WinDLL('opengl32');gl.wglGetCurrentDC.restype=C.c_void_p;dc=gl.wglGetCurrentDC();assert dc
 gdi=C.WinDLL('gdi32');gdi.GetPixelFormat.argtypes=[C.c_void_p];gdi.GetDeviceCaps.argtypes=[C.c_void_p,C.c_int];gdi.DescribePixelFormat.argtypes=[C.c_void_p,C.c_int,C.c_uint,C.c_void_p]
 pixel_format=gdi.GetPixelFormat(dc);descriptor=C.create_string_buffer(40);assert gdi.DescribePixelFormat(dc,pixel_format,40,descriptor)>0
 context_metadata=dict(pixel_format=pixel_format,pixel_format_flags=struct.unpack_from('<I',descriptor.raw,4)[0],color_bits=descriptor.raw[9],depth_bits=descriptor.raw[23],stencil_bits=descriptor.raw[24],display_refresh_hz=gdi.GetDeviceCaps(dc,116),descriptor_hex=descriptor.raw.hex())
 origin=time.perf_counter_ns()
 for i in range(frame_count):
  slot_start=time.perf_counter_ns();poll_begin=slot_start
  if pump_messages:assert gpu.nf_owned_input_poll()==1
  poll_ns=time.perf_counter_ns()-poll_begin
  sample=samples[0 if repeat_only else i%len(samples)];frame,camera,models,bounds,detail=sample
  if gpu_draw_query and query_pending is not None:
   value=C.c_uint64();gpu.nf_owned_gpu_timer_read.argtypes=[C.c_void_p];status=gpu.nf_owned_gpu_timer_read(C.byref(value))
   assert status in (0,38)
   if status==0:rows[query_pending]['gpu_draw_ms']=value.value/1e6;query_pending=None
  query_started=gpu_draw_query and query_pending is None and (not repeat_only or i==0)
  if query_started:assert gpu.nf_owned_gpu_timer_begin()==0
  draw=0;native_draw_wall_ms=None;native_draw_cpu_ms=None
  if not repeat_only or i==0:
   start=time.perf_counter_ns()
   if native_draw_timing and not repeat_only and i%21 not in (0,20):
    times=(C.c_uint64*2)();gpu.nf_owned_gpu_draw_scene_clips_timed.argtypes=gpu.nf_owned_gpu_draw_scene_clips.argtypes+[C.c_void_p]
    result=gpu.nf_owned_gpu_draw_scene_clips_timed(frame,len(frame),camera,models,bounds,detail['geometry_records'],times);native_draw_wall_ms=times[0]/1e6;native_draw_cpu_ms=None if times[1]==2**64-1 else times[1]/1e6
   else:result=gpu.nf_owned_gpu_draw(frame,len(frame)) if repeat_only or i%21 in (0,20) else gpu.nf_owned_gpu_draw_scene_clips(frame,len(frame),camera,models,bounds,detail['geometry_records'])
   assert result==0;draw=time.perf_counter_ns()-start
  if query_started:assert gpu.nf_owned_gpu_timer_end()==0;query_pending=i
  flush_begin=time.perf_counter_ns()
  if flush_before_wait:gl.glFlush()
  flush_ms=(time.perf_counter_ns()-flush_begin)/1e6
  deadline=origin+(i+1)*280896*1000000000//16777216;remaining=(deadline-time.perf_counter_ns())/1e9
  sleep_begin=time.perf_counter_ns()
  if remaining>0:time.sleep(remaining)
  sleep_end=time.perf_counter_ns()
  elapsed=C.c_uint64();stages=(C.c_uint64*3)();cpu_start=time.thread_time_ns();assert gpu.nf_owned_gpu_present_timed(struct.unpack_from('<Q',frame,24)[0],C.byref(elapsed))==0;assert gpu.nf_owned_gpu_present_stages(stages)==0
  texture=(C.c_uint64*6)();gpu.nf_owned_gpu_texture_stats.argtypes=[C.c_void_p];assert gpu.nf_owned_gpu_texture_stats(texture)==0
  rows.append(dict(gpu_query_started=query_started,gpu_draw_ms=None,native_draw_wall_ms=native_draw_wall_ms,native_draw_cpu_ms=native_draw_cpu_ms,flush_ms=flush_ms,slot_start_ns=slot_start,input_poll_ms=poll_ns/1e6,deadline_ns=deadline,sleep_ms=(sleep_end-sleep_begin)/1e6,prepresent_lateness_ms=(sleep_end-deadline)/1e6,texture_stats=list(texture),index=i,draw_ms=draw/1e6,present_ms=elapsed.value/1e6,present_thread_cpu_ms=(time.thread_time_ns()-cpu_start)/1e6,stage_ms=[v/1e6 for v in stages],completed_ns=time.perf_counter_ns()))
 gaps=[(b['completed_ns']-a['completed_ns'])/1e6 for a,b in zip(rows,rows[1:])]
 out=dict(gpu_draw_query=gpu_draw_query,query_pending=query_pending,thread_priority=observed_priority,prior_thread_priority=prior_priority,context_metadata=context_metadata,frames=frame_count,gap_median_ms=statistics.median(gaps),gap_max_ms=max(gaps),gaps_over_two_refreshes=sum(v>33.333 for v in gaps),scope=(f'Static complete captured scene: one draw,{frame_count}paced repeats, no motion proof' if repeat_only else f'Captured complete scene cyclic21poses,{frame_count}paced draws/presents, no game timing proof'),result='PASS_NATIVE_PRESENTATIONS',repeat_only=repeat_only,pump_messages=pump_messages,flush_before_wait=flush_before_wait,native_draw_timing=native_draw_timing,swap_observed=list(observed),draw_median_ms=statistics.median(x['draw_ms'] for x in rows),present_median_ms=statistics.median(x['present_ms'] for x in rows),present_max_ms=max(x['present_ms'] for x in rows),slow_presentations=sum(x['present_ms']>33.333 for x in rows),rows=rows)
 Path('work/camera/standalone-fullscene-'+('repeat' if repeat_only else 'present')+('-pumped' if pump_messages else '')+('-flushed' if flush_before_wait else '')+('-drawtimed' if native_draw_timing else '')+('-above-normal' if above_normal else '')+('-gpu-query' if gpu_draw_query else '')+'-'+str(frame_count)+'.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
finally:
 assert kernel.SetThreadPriority(thread,prior_priority)
 assert gpu.nf_owned_gpu_close()==1;prepared.close();history.close()
