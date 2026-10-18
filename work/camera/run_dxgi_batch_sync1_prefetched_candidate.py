"""Test-only wrapper for DXGI sync interval 1; standard candidate unchanged."""
import runpy
import live_native_batch_candidate as batch
batch.NativeBatchWorker.dxgi_bridge_name="owned-dx-present-sync1-bridge.dll"
runpy.run_path("work/camera/run_dxgi_batch_prefetched_candidate.py",run_name="__main__")
