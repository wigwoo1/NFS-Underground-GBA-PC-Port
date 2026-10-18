from pathlib import Path
import json

ROOT = Path(r"G:\EXTRA DATA DRIVE\Desktop\Games\Codex\NFSUG-Native-PC-Port\work\camera\prototype-runs")
runs = {
    "baseline": ROOT / "model-index-base60-clock-cleanup-20261010.json",
    "indexed_opt_in": ROOT / "model-index-candidate60-clock-cleanup-20261010.json",
}
def ms(a, b):
    assert a <= b, (a, b)
    return (b-a)/1e6

results = {}
for label, manifest_path in runs.items():
    manifest = json.loads(manifest_path.read_text())
    raw = json.loads(Path(manifest["source"]).read_text())
    stats = raw["live_observation_stats"]["whole_run_api_intervals"]
    ledger = stats["native_commit_long_intervals"]
    assert ledger["dropped"] == 0
    assert len(ledger["records"]) == manifest["coverage"]["active_intervals"]["over25"]
    requests = {}
    for req in raw["world_preparation_stage_samples"]:
        requests.setdefault((req["older"], req["newer"]), []).append(req)
    rows=[]
    for record in ledger["records"]:
        stages=record["caller_stages"]
        pair=tuple(record["transaction"]["commit"][2:4])
        matches=requests.get(pair, [])
        assert len(matches)==1, (label, record["display_index"], pair, len(matches))
        req=matches[0]
        terminal=req["terminal"][5]
        transfers=terminal["sample_transfer_rows"]
        parent_rows=terminal.get("parent_sample_rows")
        if parent_rows is None: parent_rows=[]
        assert [x["index"] for x in transfers] == list(range(len(transfers)))
        assert not parent_rows or [x["index"] for x in parent_rows] == list(range(len(parent_rows)))
        assert len(transfers)==req["prepared_sample_count"]
        assert not parent_rows or len(transfers)==len(parent_rows)
        first_child=transfers[0]
        first_parent=parent_rows[0] if parent_rows else None
        b=record["begin_ns"]
        pb=stages["pair_begin_ns"]
        pr=stages["pair_ready_ns"]
        tb=stages["preparation_take_begin_ns"]
        te=stages["preparation_take_end_ns"]
        slot=stages["slot_begin_ns"]
        assert b <= pb <= tb <= te <= pr <= slot
        dispatch=stages["hud_prefetch_dispatch"]
        assert dispatch["submitted_ns"] <= stages["hud_prefetch_wait_begin_ns"] <= dispatch["completed_ns"] <= stages["hud_prefetch_wait_end_ns"]
        prep_dispatch=record["prepared"]["renderer_dispatch"]
        consumer={x["stage"]:x["elapsed_ns"]/1e6 for x in record["prepared"]["consumer_stages"]}
        rows.append({
            "display_index": record["display_index"],
            "interval_ms": record["interval_ns"]/1e6,
            "source_pair": list(pair),
            "after_previous_commit_to_pair_begin_ms": ms(b,pb),
            "pair_acquisition_begin_to_ready_ms": ms(pb,pr),
            "preparation_take_block_ms": ms(tb,te),
            "hud_prefetch_wait_ms": ms(stages["hud_prefetch_wait_begin_ns"],stages["hud_prefetch_wait_end_ns"]),
            "pair_ready_to_first_slot_ms": ms(pr,slot),
            "child_request_submission_to_first_sample_ready_ms": ms(req["submission_begin_ns"],first_child["ready_ns"]),
            "child_start_to_first_sample_ready_ms": ms(req["started_ns"],first_child["ready_ns"]),
            "parent_receive_begin_to_sample_received_ms": ms(first_parent["receive_begin_ns"],first_parent["received_ns"]) if first_parent else None,
            "sample_ready_to_parent_received_ms": ms(first_child["ready_ns"],first_parent["received_ns"]) if first_parent else None,
            "parent_sample_copy_ms": ms(first_parent["shared_read"]["begin_ns"],first_parent["shared_read"]["copied_ns"]) if first_parent else None,
            "parent_sample_publication_ms": ms(first_parent["publication_begin_ns"],first_parent["published_ns"]) if first_parent else None,
            "parent_ack_after_publication_ms": ms(first_parent["published_ns"],first_parent["ack_sent_ns"]) if first_parent else None,
            "parent_sample_trace_retained":bool(first_parent),
            "child_ack_wait_ms": first_child["ack_wait_ns"]/1e6,
            "worker_job_total_ms": ms(req["submission_begin_ns"],req["completed_ns"]),
            "worker_queue_ms": ms(req["enqueued_ns"],req["started_ns"]),
            "worker_execution_ms": ms(req["started_ns"],req["completed_ns"]),
            "render_prepare_queue_ms": ms(prep_dispatch["submitted_ns"],prep_dispatch["started_ns"]),
            "render_prepare_job_ms": ms(prep_dispatch["started_ns"],prep_dispatch["completed_ns"]),
            "consumer_stages_ms": consumer,
        })
    results[label]={
        "raw_source":manifest["source"],
        "long_interval_count":len(rows),
        "live_interval_summary":{k:stats[k] for k in ("mean_ms","max_ms","over_25ms","over_33_333ms","over_50ms")},
        "rows":rows,
    }
out={
    "result":"PASS_PAIR_READINESS_PARTITION",
    "runs":results,
    "scope":"Complete retained >25ms rows in matched 60s normal-path baseline and indexed opt-in runs. Pair and worker stages are nested wall spans, not exclusive CPU/GIL causality; parent sample receive rows are reported only when retained in the source trace. No physical display scanout or smooth-60 qualification.",
}
dest=ROOT / "pair-readiness-stalls-20261010.json"
dest.write_text(json.dumps(out,indent=2))
for label,data in results.items():
    print(label, data["live_interval_summary"])
    for row in data["rows"]:
        print(json.dumps(row,separators=(",",":")))
print("saved",dest)

