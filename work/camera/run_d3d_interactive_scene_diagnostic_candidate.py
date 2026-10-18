"""Interactive complete-scene diagnostic; fixed recorded samples, not playable."""
from pathlib import Path
import argparse,ctypes as C,json,time,traceback,os
root=Path(__file__).resolve().parents[2];os.chdir(root)
a=argparse.ArgumentParser();a.add_argument('--hold-seconds',type=float,default=8);args=a.parse_args();assert 0<=args.hold_seconds<=60
source=(root/'work/camera/test_d3d_flip_window_scene_candidate.py').read_text()
source=source.replace('import ctypes as C,json,zlib,hashlib,threading','import ctypes as C,json,zlib,hashlib,threading,time')
source=source.replace('present_results=[];','present_durations_ns=[];present_results=[];')
source=source.replace('present_status=d.nf_d3d_present();','present_start=time.perf_counter_ns();present_status=d.nf_d3d_present();present_durations_ns.append(time.perf_counter_ns()-present_start);')
# Hold each captured image briefly, not interpolated gameplay. This permits visual inspection.
source=source.replace("  elif kind=='end_frame':", "  elif kind=='end_frame':")
source=source.replace('   assert d.nf_d3d_read(rgb,len(rgb))==0;', '''   hold_deadline=time.perf_counter()+hold_seconds/5
   while time.perf_counter()<hold_deadline:
    state=(C.c_uint64*7)();pump=d.nf_d3d_window_pump(window,state)
    if pump:raise RuntimeError('Diagnostic window closed during inspection')
    time.sleep(.01)
   assert d.nf_d3d_read(rgb,len(rgb))==0;''')
source=source.replace('r=dict(window_telemetry=',"r=dict(present_call_durations_ns=present_durations_ns,diagnostic_kind='Five recorded scene samples held for inspection; not playable or smooth-motion test',window_telemetry=")
source=source.replace("d3d-flip-window-scene-component.json","d3d-interactive-scene-diagnostic.json")
ns={'hold_seconds':args.hold_seconds};failure=None
try:exec(compile(source,'interactive_scene','exec'),ns)
except BaseException:
 failure=traceback.format_exc();(root/'work/camera/prototype-runs/d3d-interactive-scene-failure.json').write_text(json.dumps(dict(error=failure,scope='Diagnostic failed; no visible presentation success implied.'),indent=2));raise
finally:
 d=ns.get('d');window=ns.get('window');user=ns.get('user')
 if d:d.nf_d3d_close()
 if user and window:user.DestroyWindow(window)
