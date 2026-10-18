"""Read-only early-render planning must never advance original game updates."""
from pathlib import Path
import ctypes as C,json,math
class Clock(C.Structure):_fields_=[('origin',C.c_uint64),('last',C.c_uint64),('simulated',C.c_uint64),('next_display',C.c_uint64),('base',C.c_uint32),('active',C.c_uint32),('delay',C.c_double)]
class Plan(C.Structure):_fields_=[('simulation_steps',C.c_uint32),('present',C.c_uint32),('display_index',C.c_uint64),('skipped_displays',C.c_uint64),('deadline_ns',C.c_uint64),('next_wake_ns',C.c_uint64),('source_target',C.c_double)]
class Preparation(C.Structure):_fields_=[('eligible',C.c_uint32),('display_index',C.c_uint64),('deadline_ns',C.c_uint64),('next_wake_ns',C.c_uint64),('source_target',C.c_double)]
p=Path('work/camera');d=C.CDLL(str((p/'frame_clock.dll').resolve()))
d.nf_frame_clock_start.argtypes=[C.POINTER(Clock),C.c_uint64,C.c_uint32,C.c_double]
d.nf_frame_clock_poll.argtypes=[C.POINTER(Clock),C.c_uint64,C.POINTER(Plan)]
d.nf_frame_clock_prepare.argtypes=[C.POINTER(Clock),C.c_uint64,C.c_uint64,C.POINTER(Preparation)]
cases=0;steps=0
for lead in (1000000,4000000,8000000,15000000):
    clock=Clock();assert d.nf_frame_clock_start(C.byref(clock),0,8842,8)
    plan=Plan();assert d.nf_frame_clock_poll(C.byref(clock),0,C.byref(plan))
    for index in range(1,601):
        deadline=(index*1000000000+59)//60;before=bytes(clock)
        for now,eligible in ((deadline-lead-1,0),(deadline-lead,1),(deadline-1,1),(deadline,0),(deadline+1,0)):
            prepared=Preparation();assert d.nf_frame_clock_prepare(C.byref(clock),now,lead,C.byref(prepared))
            assert bytes(clock)==before and prepared.eligible==eligible
            assert prepared.deadline_ns==deadline and prepared.display_index==index
            assert math.isclose(prepared.source_target,8842+index*16777216/(280896*60)-8,abs_tol=1e-9)
            cases+=1
        control=Clock.from_buffer_copy(before);other=Plan()
        assert d.nf_frame_clock_poll(C.byref(control),deadline,C.byref(other))
        assert d.nf_frame_clock_poll(C.byref(clock),deadline,C.byref(plan))
        assert bytes(clock)==bytes(control) and bytes(plan)==bytes(other)
        assert clock.simulated==deadline*16777216//(1000000000*280896)
        steps+=plan.simulation_steps
    prepared=Preparation();saved=bytes(prepared);before=bytes(clock)
    for now,lead_bad in ((clock.last-1,4000000),(clock.last,15000001)):
        assert not d.nf_frame_clock_prepare(C.byref(clock),now,lead_bad,C.byref(prepared))
        assert bytes(clock)==before and bytes(prepared)==saved
report=dict(result='PASS',window_cases=cases,original_steps_unchanged=steps,atomic_rejections=8,
            scope='Early preparation windows preserve exact original clock plans/state; eligible only before upcoming presentation deadline. No owned scene availability, GPU rendering, live pacing or physical input proof.')
(p/'frame-preparation-tests.json').write_text(json.dumps(report,indent=2));print(report)
