"""Test-only wrapper collecting DXGI GetFrameStatistics after worker shutdown."""
import runpy
import live_native_batch_candidate as batch
cls=batch.NativeBatchWorker
cls.dxgi_bridge_name="owned-dx-present-sync1-frame-stats-bridge.dll"
previous_close=cls.close
def close_with_frame_stats(self):
    try:
        return previous_close(self)
    finally:
        bridge=getattr(self,"dxgi_bridge",None)
        if bridge is not None and hasattr(bridge,"nf_dx_bridge_frame_stats"):
            values=(batch.U*11)()
            rc=bridge.nf_dx_bridge_frame_stats(values)
            evidence=getattr(self,"shutdown_evidence",None)
            if evidence is not None: evidence["dxgi_frame_statistics_candidate"]={"result":int(rc),"values":list(values)}
cls.close=close_with_frame_stats
runpy.run_path("work/camera/run_dxgi_batch_prefetched_candidate.py",run_name="__main__")

