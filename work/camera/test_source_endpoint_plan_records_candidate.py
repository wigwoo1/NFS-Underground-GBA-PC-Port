"""Compare endpoint record reuse from a validated motion plan against reparsing."""
import ctypes as C
import hashlib
import importlib
import json
import statistics
import struct
import time
from pathlib import Path

from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_motion_scene import MotionScene
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_prepared_world_motion import PreparedWorldMotion
from owned_motion_pairs import _record_cache
from owned_progressive_source_samples_candidate import source_library_owner, projection_table_owner

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "outputs/nfsug-native-renderer/camera-research"
CAPTURE = Path("work/camera/prototype-runs/owned-native-1791267744113946700.json")
capture = json.loads(CAPTURE.read_text())
fa, fb = capture["wall_diagnostic_frames"][:2]
graph_a = ClosedGraph.decode(Path(fa["graph"]).read_bytes())
graph_b = ClosedGraph.decode(Path(fb["graph"]).read_bytes())
scene_a = ClosedSupplements.decode(Path(fa["supplements"]).read_bytes(), graph_a)
scene_b = ClosedSupplements.decode(Path(fb["supplements"]).read_bytes(), graph_b)
rom_path = Path("G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba")
rom = rom_path.read_bytes()
table = projection_table_owner()
history = EndpointRoadPlanner(rom, table.values)
roads, _ = history.plan(graph_a)
prepared = PreparedWorldMotion(
    Path(fa["regenerated"]).read_bytes(), Path(fb["regenerated"]).read_bytes(),
    MotionScene(graph_a, scene_a), MotionScene(graph_b, scene_b), history, roads, rom)
motion = prepared.pair.portal.motion
plan = motion.arguments[0]

def normalized(result):
    anchors, classifiers = result
    anchor_state = (anchors.offsets, anchors.raw, anchors.preanchored_keys)
    names = ("vertices", "faces", "endpoint_points", "projection_residual", "exact",
             "residual", "centers", "scales")
    classifier_state = {
        key: (type(value).__module__, type(value).__qualname__,
              tuple((name, getattr(value, name)) for name in names),
              bytes(value.native_vertices))
        for key, value in classifiers.items()
    }
    payload = repr((anchor_state, classifier_state)).encode()
    return hashlib.sha256(payload).hexdigest(), anchor_state, classifier_state

def measured(function, count=3):
    rows = []
    last = None
    for _ in range(count):
        _record_cache.entries = []
        trace = []
        begin = time.perf_counter_ns()
        last = function(trace)
        rows.append((time.perf_counter_ns() - begin) / 1e6)
    return last, rows

module = importlib.import_module("owned_source_presentation_batch_candidate")
old_records = module.records
function = module.prepare_source_models
gpu = source_library_owner()

def legacy(trace):
    return function(prepared, gpu, table, trace)

baseline, baseline_ms = measured(legacy)
samples_module = importlib.import_module("owned_progressive_source_samples_candidate")
from owned_source_endpoint_plan_records_candidate import install
install_evidence = install()
optimized_prepare = samples_module.prepare_source_models
def optimized(trace):
    return optimized_prepare(prepared, gpu, table, trace)
original_sample = prepared.sample
def endpoint_scene_assembly_must_not_run(_alpha):
    raise AssertionError("Endpoint plan path unexpectedly assembled a throwaway world")
prepared.sample = endpoint_scene_assembly_must_not_run
try:
    candidate, candidate_ms = measured(optimized)
finally:
    prepared.sample = original_sample

before = normalized(baseline)
after = normalized(candidate)
assert before == after, "Plan-owned endpoint rows changed classification/anchor results"
hits = list(samples_module.endpoint_plan_records_calls)
assert len(hits) == len(candidate_ms) and all(len(row) == 2 for row in hits), hits
assert motion.older is prepared.pair.portal.motion.older
assert motion.newer is prepared.pair.portal.motion.newer
assert [motion.sample(a)[0] is motion.older for a in (0,)] == [True]
assert [motion.sample(a)[0] is motion.newer for a in (1,)] == [True]

result = {
    "result": "PASS_SOURCE_ENDPOINT_PLAN_RECORD_PARITY",
    "baseline_signature": before[0],
    "candidate_signature": after[0],
    "endpoint_record_counts": [len(plan[k]["records"]) for k in ("older", "newer")],
    "endpoint_refreshes": [plan[k]["refresh"] for k in ("older", "newer")],
    "plan_record_identity_hits": sum(map(len, hits)),
    "endpoint_scene_assembly_skipped": True,
    "candidate_install": install_evidence,
    "candidate_call_refreshes": hits,
    "baseline_ms": baseline_ms,
    "candidate_ms": candidate_ms,
    "baseline_median_ms": statistics.median(baseline_ms),
    "candidate_median_ms": statistics.median(candidate_ms),
    "scope": "Captured source pair; endpoint classifier/anchor state exact parity, no live cadence claim.",
}
out = Path(f"work/camera/prototype-runs/source-endpoint-plan-record-parity-{time.time_ns()}.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2))
prepared.close()
history.close()
assert hashlib.sha256(rom_path.read_bytes()).hexdigest() == hashlib.sha256(rom).hexdigest()
print(json.dumps(result, indent=2))
