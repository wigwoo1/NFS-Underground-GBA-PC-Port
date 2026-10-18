"""Test-only full-scene DXGI run using the previously parity-checked clip transaction."""
import io
import json
import runpy
from contextlib import redirect_stdout
from pathlib import Path

import owned_camera_clip_transaction_install_candidate as road_transaction

road_transaction.install()
captured = io.StringIO()
with redirect_stdout(captured):
    runpy.run_path("work/camera/run_dxgi_batch_prefetched_candidate.py", run_name="__main__")
output = captured.getvalue()
print(output, end="")
reports = [
    Path(line.strip())
    for line in output.splitlines()
    if "owned-native-" in line and line.strip().endswith(".json")
]
if reports:
    report_path = reports[-1]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["road_clip_transaction_candidate"] = dict(
        enabled=True,
        calls=road_transaction.stats["calls"],
        scope="test-only wrapper; exact-output transaction previously passed full sample parity",
    )
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
