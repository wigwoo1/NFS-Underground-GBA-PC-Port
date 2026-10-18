"""Test-only DXGI frame-statistics capture for the CPU batch probe."""
import json, runpy
import live_native_batch_cpu_probe_candidate as batch
cls=batch.NativeBatchWorker
original_before=cls._before_gpu_close
captured={}
def before_gpu_close(self):
    bridge=getattr(self,"dxgi_bridge",None)
    if bridge is not None and hasattr(bridge,"nf_dx_bridge_frame_stats"):
        values=(batch.U*11)()
        rc=bridge.nf_dx_bridge_frame_stats(values)
        captured["frame_statistics"]={"result":int(rc),"values":list(values)}
    return original_before(self)
cls._before_gpu_close=before_gpu_close
original_dumps=json.dumps
def dumps(obj,*args,**kwargs):
    if isinstance(obj,dict) and "presentation_samples" in obj and "smooth_60fps_verified" in obj:
        obj["dxgi_frame_statistics_candidate"]=captured.get("frame_statistics")
    return original_dumps(obj,*args,**kwargs)
json.dumps=dumps
runpy.run_path("work/camera/run_dxgi_batch_sync1_cpu_probe_candidate.py",run_name="__main__")
