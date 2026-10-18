import json
from pathlib import Path
from owned_slow_process_rows_candidate import ProcessRows
r=json.loads(Path("work/camera/prototype-runs/owned-native-1791574395774015300.json").read_text())
s=r["preparation_retention"]["slow_process_intervals"]["records"][0]
child=dict(child_boundaries=s["child_boundaries"],child_gc_rows=s["child_gc_rows"],child_gc_dropped=s["child_gc_dropped"],send_ns=s["child_send_ns"],precompute_ns=s["child_precompute_ns"],construct_advance_ns=s["child_construct_ns"],shared_write=dict(begin_ns=10,end_ns=20,thread_cycles=30,payload_bytes=40))
row=dict(s,child_stages=child,parent_completed_ns=s["end_ns"])
rows=ProcessRows(2,max_record_bytes=1048576,slow_threshold_ns=1,slow_capacity=2)
rows.append(row);child["shared_write"]["payload_bytes"]=999
saved=rows.stats()["slow_process_intervals"];assert saved["dropped"]==0 and saved["records"][0]["shared_write"]["payload_bytes"]==40
rows.append(row);rows.append(row);assert rows.stats()["slow_process_intervals"]["dropped"]==1
out=dict(result="PASS_PRIVATE_BOUNDED_SHARED_WRITE_RETENTION",scope="Existing child trace copied into serialized bounded slow-request evidence; mutation isolation and capacity accounting. No gameplay performance claim.")
Path("outputs/nfsug-native-renderer/camera-research/shared-write-retention-component-20261009.json").write_text(json.dumps(out,indent=2));print(out["result"])
