"""A/B the optional road camera/visibility subtrace on captured scene ownership."""
from pathlib import Path
import hashlib
import json
import sys

sys.path.insert(0, str(Path("work/camera").resolve()))
setup_source = (
    Path("work/camera/test_external_changed_parent_exit.py")
    .read_text()
    .split("gpu=C.CDLL")[0]
    .replace("1791308040881565000", "1791576492416199100")
    .replace(
        "from owned_prepared_world_motion import PreparedWorldMotion",
        "from owned_prepared_world_segmented_candidate import PreparedWorldMotion",
    )
)
setup = {}
exec(setup_source, setup)
setup["prepared"].close()
setup["history"].close()

from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
import owned_sampled_road_sequence as road_module

alphas = (0.13501430343535606, 0.4668337510442774, 0.7986531986531986)


def create_prepared():
    history = EndpointRoadPlanner(setup["rom"], setup["table"])
    older_roads, _ = history.plan(setup["scenes"][0].graph)
    prepared = PreparedWorldMotion(
        *setup["frames"], *setup["scenes"], history, older_roads, setup["rom"]
    )
    return history, prepared


def fingerprint(sample):
    frame, camera, models, bounds, detail = sample
    h = hashlib.sha256(bytes(frame))
    for values in (camera, models, bounds):
        if values is not None:
            h.update(bytes(values))
    h.update(json.dumps(detail, sort_keys=True).encode())
    return h.hexdigest()


road_module._ROAD_VISIBILITY_FINE_TRACE = False
history, baseline = create_prepared()
try:
    expected = [fingerprint(baseline.sample(alpha)) for alpha in alphas]
finally:
    baseline.close()
    history.close()

road_module._ROAD_VISIBILITY_FINE_TRACE = True
history, traced = create_prepared()
rows = []
try:
    actual = []
    for alpha in alphas:
        sample = traced.sample(alpha)
        actual.append(fingerprint(sample))
        stages = [
            row for row in traced.roads._last_road_stages
            if row["name"] == "camera_and_visibility"
        ]
        for stage in stages:
            detail = stage.get("visibility_substages")
            assert detail and [x["name"] for x in detail] == [
                "far_depths", "camera_projection", "stream_count"
            ]
            assert all(x["wall_ns"] >= 0 for x in detail)
            assert all(a["completed_ns"] == b["started_ns"] for a, b in zip(detail, detail[1:]))
            rows.append(dict(alpha=alpha, descriptor=stage["descriptor"],
                             camera_visibility_ns=stage["wall_ns"], substage=detail))
    assert actual == expected, "Fine tracing changed a sampled frame or its metadata"
finally:
    traced.close()
    history.close()
    road_module._ROAD_VISIBILITY_FINE_TRACE = False

report = dict(
    result="PASS_ROAD_VISIBILITY_SUBSTAGE_BYTE_PARITY",
    samples=len(alphas),
    descriptors=len(rows),
    exact_output_fingerprints=actual,
    expected_fingerprints=expected,
    timings=rows,
    scope="Captured scene pair component A/B only; instrumentation is opt-in and this is not a live cadence test.",
)
out = Path("work/camera/prototype-runs/road-visibility-fine-trace-fixture-20261011.json")
out.write_text(json.dumps(report, indent=2))
print(report["result"], "samples", len(alphas), "descriptors", len(rows), "report", out)
