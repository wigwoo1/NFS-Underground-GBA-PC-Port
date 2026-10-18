"""Isolated direct GL fullscene presentation, original logic, precise local handoff."""
import ctypes as C
from pathlib import Path
root=Path('work/camera').resolve();original_cdll=C.CDLL;original_pydll=C.PyDLL
mapping={'owned-frame-handoff.dll':'owned-frame-handoff-precise-candidate.dll','owned-draw-commit-candidate.dll':'owned-draw-commit-precise-candidate.dll'}
loads=[]
def mapped(name):
 p=Path(name)
 if p.parent.resolve()==root and p.name in mapping:
  replacement=str(p.with_name(mapping[p.name]));loads.append([str(p),replacement]);return replacement
 return name
C.CDLL=lambda name,*a,**k:original_cdll(mapped(name),*a,**k)
C.PyDLL=lambda name,*a,**k:original_pydll(mapped(name),*a,**k)
from owned_compact_diagnostics import CompactPresentationDiagnostics
from live_source_batch_candidate import SourceBatchWorker
from owned_world_preparation_service import WorldPreparationService
SourceBatchWorker.result_ledger_factory=CompactPresentationDiagnostics
WorldPreparationService.compact_stage_diagnostics=True
SourceBatchWorker.dxgi_enabled=False
import runpy,json,time
from pathlib import Path
import live_native_batch_candidate as original
from live_source_batch_candidate import SourceBatchWorker as NativeBatchWorker
original.NativeBatchWorker=NativeBatchWorker
import owned_world_preparation_service as preparation
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
preparation.PrecomputedWorldSamples=PrecomputedSourceWorldSamples
NativeBatchWorker.batch_bridge_name='owned-batch-present-precise-candidate.dll'
NativeBatchWorker.gpu_ready_enabled=False
NativeBatchWorker.gpu_queued_enabled=False
NativeBatchWorker.queued_ordered_gpu=False
NativeBatchWorker.queued_draw_probe_enabled=False
NativeBatchWorker.ready_adapter_name='owned-gpu-ready-bounded-candidate.dll'
NativeBatchWorker.gpu_renderer_name='owned-gpu-playable-input-profile-candidate.dll'
def after_close(self,gpu):
 import ctypes as C
 gpu.nf_owned_gpu_pool_stats.argtypes=[C.c_void_p];gpu.nf_owned_gpu_pool_fences.argtypes=[C.c_void_p]
 targets=(C.c_uint64*5)();fences=(C.c_uint64*4)()
 assert gpu.nf_owned_gpu_pool_stats(targets)==0 and list(targets)==[0]*5
 assert gpu.nf_owned_gpu_pool_fences(fences)==0 and fences[0]==fences[1] and fences[3]==0
 path=Path('work/camera/prototype-runs')/('pool-cleanup-'+str(time.time_ns())+'.json');path.write_text(json.dumps(dict(targets=list(targets),fences=list(fences)),indent=2));print(path)
NativeBatchWorker._after_gpu_close=after_close
runpy.run_path('work/camera/run_native_batch_candidate.py',run_name='__main__')
