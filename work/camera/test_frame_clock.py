from pathlib import Path
import ctypes as C,json,math
class Clock(C.Structure):_fields_=[('origin',C.c_uint64),('last',C.c_uint64),('simulated',C.c_uint64),('next_display',C.c_uint64),('base',C.c_uint32),('active',C.c_uint32),('delay',C.c_double)]
class Plan(C.Structure):_fields_=[('simulation_steps',C.c_uint32),('present',C.c_uint32),('display_index',C.c_uint64),('skipped_displays',C.c_uint64),('deadline_ns',C.c_uint64),('next_wake_ns',C.c_uint64),('source_target',C.c_double)]
root=Path('work/camera');d=C.CDLL(str((root/'frame_clock.dll').resolve()))
d.nf_frame_clock_start.argtypes=[C.POINTER(Clock),C.c_uint64,C.c_uint32,C.c_double]
d.nf_frame_clock_poll.argtypes=[C.POINTER(Clock),C.c_uint64,C.POINTER(Plan)]
clock=Clock();p=Plan();origin=123456789;assert d.nf_frame_clock_start(C.byref(clock),origin,8842,5)
count=steps=zero_step_displays=0
for tick in range(60*1800+1):
 elapsed=(tick*10**9+59)//60
 assert d.nf_frame_clock_poll(C.byref(clock),origin+elapsed,C.byref(p))
 expected=elapsed*16777216//(10**9*280896)
 assert p.present and p.display_index==tick and not p.skipped_displays
 assert clock.simulated==expected and p.simulation_steps<=1
 assert p.deadline_ns==origin+elapsed and p.next_wake_ns>origin+elapsed
 assert math.isclose(p.source_target,8842+tick*16777216/(280896*60)-5,abs_tol=1e-9)
 steps+=p.simulation_steps;zero_step_displays+=p.simulation_steps==0;count+=1
assert steps<108000 and steps==1800*16777216//280896
# A stall caps work per poll and skips overdue presentation, never simulation.
assert d.nf_frame_clock_start(C.byref(clock),0,0,5)
assert d.nf_frame_clock_poll(C.byref(clock),0,C.byref(p)) and p.present
caught=0;polls=0
while True:
 assert d.nf_frame_clock_poll(C.byref(clock),10*10**9,C.byref(p));polls+=1
 assert p.simulation_steps<=4;caught+=p.simulation_steps
 if p.present:break
 assert p.next_wake_ns==10*10**9
assert caught==10*16777216//280896 and p.display_index==600 and p.skipped_displays==599
# Restart establishes a fresh time origin without catching up paused wall time.
assert d.nf_frame_clock_start(C.byref(clock),100*10**9,42,5)
assert d.nf_frame_clock_poll(C.byref(clock),100*10**9,C.byref(p)) and p.simulation_steps==0 and p.source_target==37
before=bytes(clock);output=bytes(p)
assert not d.nf_frame_clock_poll(C.byref(clock),99*10**9,C.byref(p))
assert bytes(clock)==before and bytes(p)==output
assert not d.nf_frame_clock_start(C.byref(clock),0,0,float('nan')) and bytes(clock)==before
report={'result':'PASS','virtual_duration_seconds':1800,'presentation_slots_verified':count,'original_simulation_refreshes':steps,'slots_without_simulation_step':zero_step_displays,'stall_recovery_polls':polls,'stall_simulation_refreshes_preserved':caught,'overdue_presentation_slots_skipped':599,'pause_restart_and_failure_atomicity':True,'scope':'Deterministic scheduler tests only; real wall-clock scheduling and display pacing not yet measured.'}
(root/'frame-clock-tests.json').write_text(json.dumps(report,indent=2));print(report)
