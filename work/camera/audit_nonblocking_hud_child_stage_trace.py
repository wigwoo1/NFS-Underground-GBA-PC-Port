import json, statistics, sys
from pathlib import Path

raw_path, out_path = map(Path, sys.argv[1:3])
raw = json.loads(raw_path.read_text())
whole = raw["live_observation_stats"]["whole_run_api_intervals"]
native = whole["native_commit_intervals"]
long = whole["native_commit_long_intervals"]

def summary(values):
    values = sorted(values)
    if not values:
        return {"count": 0}
    return {
        "count": len(values),
        "median_ms": statistics.median(values),
        "p95_ms": values[int((len(values)-1)*0.95)],
        "max_ms": values[-1],
    }

jobs = [j for j in raw["world_preparation_stage_samples"]
        if 10952 <= j["newer"] <= 10968 and j["terminal"][5]["fine_trace"]]
assert [(j["older"], j["newer"]) for j in jobs] == [
    (10952, 10958), (10958, 10963), (10963, 10968)]
sample_stage_values, assembly_stage_values = {}, {}
pairs = []
for job in jobs:
    d = job["terminal"][5]
    samples = []
    parent = {r["index"]: r for r in job["parent_sample_rows"]}
    for sample in d["sample_timings"]:
        src = {s["name"]: s for s in sample["source_sample_stages"]}
        assm = {s["name"]: s for s in sample["assembly_stages"]}
        for name, stage in src.items():
            sample_stage_values.setdefault(name, []).append(stage["wall_ns"]/1e6)
        for name, stage in assm.items():
            assembly_stage_values.setdefault(name, []).append(stage["wall_ns"]/1e6)
        visible = next(s for s in sample["assembly_stages"]
                       if s["name"] == "main_graph_surfaces")
        row = {
            "alpha": sample["alpha"],
            "sample_total_ms": sample["wall_ns"]/1e6,
            "source_stages_ms": {k: v["wall_ns"]/1e6 for k, v in src.items()},
            "assembly_stages_ms": {k: v["wall_ns"]/1e6 for k, v in assm.items()},
            "wall_visibility_stages_ms": {
                s["name"]: s["wall_ns"]/1e6 for s in visible["visibility_stages"]
            },
            "wall_candidate_count": next(
                s["count"] for s in visible["visibility_stages"]
                if s["name"] == "candidate_generation"),
            "wall_visible_count": next(
                s["count"] for s in visible["visibility_stages"]
                if s["name"] == "selection_and_order"),
        }
        samples.append(row)
    transfer = d["sample_transfer_rows"]
    first = transfer[0]
    pfirst = parent[first["index"]]
    pairs.append({
        "pair": [job["older"], job["newer"]],
        "worker_ms": (job["completed_ns"]-job["started_ns"])/1e6,
        "world_construct_ms": (d["constructed_ns"]-d["initialized_ns"])/1e6,
        "world_construct_cycles": d["world_construct_thread_cycles"],
        "sample_count": len(samples),
        "first_sample_prepare_ms": first["prepare_since_ack_ns"]/1e6,
        "first_sample_cycles": first["prepare_thread_cycles"],
        "parent_receive_before_first_writer_ms":
            (first["shared_write"]["begin_ns"]-pfirst["receive_begin_ns"])/1e6,
        "samples": samples,
        "construct_stages_ms": {
            s["name"]: s["wall_ns"]/1e6 for s in d["construct_stages"]
        },
    })

out = {
    "result": "PASS_NARROW_CHILD_STAGE_TRACE_ACCOUNTING",
    "source_raw": str(raw_path),
    "selected_source_pairs": [[j["older"], j["newer"]] for j in jobs],
    "whole_run": {
        "result": raw["result"],
        "original_updates": raw["original_updates"],
        "presentations": raw["presentations"],
        "mean_ms": whole["mean_ms"],
        "max_ms": whole["max_ms"],
        "over_25ms": whole["over_25ms"],
        "over_33_333ms": whole["over_33_333ms"],
        "over_50ms": whole["over_50ms"],
        "smooth_60fps_verified": raw["smooth_60fps_verified"],
        "physical_controller_verified": raw["physical_controller_verified"],
        "native_intervals": native["count"],
        "native_over_25ms": native["over25"],
        "native_over_33ms": native["over33"],
        "native_over_50ms": native["over50"],
        "native_mean_ms": native["mean_ms"],
        "native_max_ms": native["max_ms"],
        "native_long_count": long["total"],
        "native_long_dropped": long["dropped"],
        "background_worker": raw["background_copy_shutdown"],
        "preparation_shutdown": raw["frame_preparation_shutdown"],
        "hud_cleanup": raw["hud_lease_cleanup"],
    },
    "sample_stage_summary_ms": {
        name: summary(values) for name, values in sorted(sample_stage_values.items())
    },
    "assembly_stage_summary_ms": {
        name: summary(values) for name, values in sorted(assembly_stage_values.items())
    },
    "pairs": pairs,
    "scope": (
        "Fine tracing selected only newer source identities 10952..10968, "
        "but CPU/cycle counters were enabled process-wide. This is diagnostic "
        "stage evidence only; the run is not a frame-rate qualification. "
        "Elapsed spans overlap across parent/child; do not sum as exclusive CPU."
    ),
}
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(out, indent=2))
print(out["result"], "pairs", len(pairs), "samples", sum(p["sample_count"] for p in pairs))
print(json.dumps({
    "whole_run": out["whole_run"],
    "sample_stage_summary_ms": out["sample_stage_summary_ms"],
    "assembly_stage_summary_ms": out["assembly_stage_summary_ms"],
}, indent=2))
print("saved", out_path)


