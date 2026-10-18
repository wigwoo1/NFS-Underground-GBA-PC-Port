"""Opt-in native presentation floor diagnostic; retain post-close timer evidence."""
import os,runpy,ctypes as C,json,time
from pathlib import Path
assert os.environ.get('NFSUG_PRESENT_FLOOR')=='1' and os.environ.get('NFSUG_CLOCK_PRESENT')=='1'
runpy.run_path('work/camera/run_native_sky_reader_bulk.py',run_name='__main__')
import owned_world_stream_linear_backend_install_candidate as backend
assert len(backend.loads)==1 and Path(backend.loads[0]).name==('owned-d3d-start-floor-present-transaction-candidate.dll' if os.environ.get('NFSUG_PRESENT_FLOOR_START')=='1' else 'owned-d3d-floor-present-transaction-candidate.dll')
d=C.CDLL(backend.loads[0]);fn=d.nf_d3d_floor_stats;fn.argtypes=[C.c_void_p,C.c_size_t]
q=(C.c_uint64*8)();assert fn(q,64)==0 and q[0]>0 and q[1]>0 and q[7]==0 and q[6]==0
for size in (0,8,63,65):
 sentinel=(C.c_uint64*8)(*([123]*8));assert fn(sentinel,size)!=0 and list(sentinel)==[123]*8
assert fn(None,64)!=0
out=dict(result='PASS_EXECUTED_FLOOR_COUNTERS_AND_TIMER_CLOSE',library=backend.loads[0],stats=list(q),scope='Native floor executed and timer closed. No original throughput/latency, fullscene cadence or physical scanout qualification.')
path=Path('work/camera/prototype-runs')/('floor-present-cleanup-'+str(time.time_ns())+'.json');path.write_text(json.dumps(out,indent=2));print('FLOOR_CLEANUP',path,list(q),flush=True)

