"""Reuse endpoint record tables already validated by PreparedMotionPair.

This opt-in candidate reads exact record rows from the immutable validated
endpoint plan, avoiding two throwaway endpoint-world assemblies. It keeps the
original ownership/classification routine and guards frame identity/header.
"""
import importlib
import struct
import time


def install():
    samples = importlib.import_module("owned_progressive_source_samples_candidate")
    original_prepare = samples.prepare_source_models
    samples.endpoint_plan_records_calls = []

    def prepare_source_models(pair, gpu, table, trace=None):
        motion = pair.pair.portal.motion
        plan = motion.arguments[0]
        if type(motion.older) is not bytes or type(motion.newer) is not bytes:
            raise ValueError("Endpoint plan requires immutable validated frames")
        endpoint_frames = (("older", motion.older), ("newer", motion.newer))
        for name, frame in endpoint_frames:
            refresh = struct.unpack_from("<I", frame, 4)[0]
            epoch = struct.unpack_from("<Q", frame, 24)[0]
            endpoint = plan[name]
            if endpoint["refresh"] != refresh or endpoint["epoch"] != epoch:
                raise ValueError("Prepared endpoint record identity mismatch")
            if not isinstance(endpoint["records"], list):
                raise ValueError("Prepared endpoint records unavailable")
        endpoint_rows = []
        hits = []
        for name, frame in endpoint_frames:
            entry = plan[name]
            magic, refresh, _geometry_bytes, _header_bytes, _base_bytes, _tail_bytes, epoch, ticks = struct.unpack_from(
                "<6I2Q", frame)
            if (magic != 0x3346474E or refresh != entry["refresh"] or
                    epoch != entry["epoch"] or ticks != entry["ticks"]):
                raise ValueError("Prepared endpoint frame header mismatch")
            endpoint_rows.append(entry["records"])
            hits.append(refresh)
        metadata_ns = time.perf_counter_ns()
        result = original_prepare(pair, gpu, table, trace, endpoint_rows=tuple(endpoint_rows))
        samples.endpoint_plan_records_calls.append(tuple(hits))
        if trace is not None:
            endpoint_stage = next((stage for stage in trace
                                   if stage.get("name") == "endpoint_sampling_and_decode"), None)
            if endpoint_stage is not None:
                endpoint_stage["endpoint_world_assembly_stages"] = list(
                    ())
                endpoint_stage["nested_model_owner_stages"] = list(
                    getattr(pair.pair, "_model_owner_stages", ()))
                endpoint_stage["endpoint_scene_assembly_skipped"] = True
            trace.append(dict(name="validated_endpoint_plan_record_reuse", started_ns=metadata_ns,
                              completed_ns=metadata_ns, wall_ns=0, thread_cycles=0,
                metadata_only=True, refreshes=tuple(hits), endpoint_scene_assembly_skipped=True,
                record_counts=tuple(len(plan[name]["records"]) for name, _ in endpoint_frames)))
        return result

    samples.prepare_source_models = prepare_source_models
    return dict(installed=True, source="validated PreparedMotionPair endpoint rows",
                exact_endpoint_identity_guard=True, endpoint_header_guard=True,
                endpoint_scene_assembly_skipped=True, fallback_for_other_frames=True)
