"""Test-only prewarm of the scenery builder inside the process that uses it."""
import json
import os
import runpy
from pathlib import Path
import owned_process_preparation_service as preparation_service

os.environ["NF_PREWARM_SCENERY_RECORD_BUILDER"] = "1"
_warm_start = preparation_service.ProcessPreparationService.warm_start


def _warm_start_with_builder(self, *args, **kwargs):
    self.prewarm_scenery_builder = True
    return _warm_start(self, *args, **kwargs)


preparation_service.ProcessPreparationService.warm_start = _warm_start_with_builder
runpy.run_path("work/camera/run_dxgi_batch_prefetched_candidate.py", run_name="__main__")

reports = list(Path("work/camera/prototype-runs").glob("owned-native-*.json"))
if reports:
    report_path = max(reports, key=lambda path: path.stat().st_mtime_ns)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["model_record_builder_prewarm_candidate"] = dict(
        enabled=True,
        evidence=(report.get("startup_readiness") or {}).get("model_record_builder_prewarm"),
        scope="test-only opt-in; ModelRecordBuilder initialized on the preparation child process before the live simulation clock",
    )
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Builder-prewarm evidence written to {report_path}")
