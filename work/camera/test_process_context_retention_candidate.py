import json
from pathlib import Path
from owned_slow_process_rows_candidate import ProcessRows
r=json.loads(Path("work/camera/prototype-runs/owned-native-1791574395774015300.json").read_text())
s=r["preparation_retention"]["slow_process_intervals"]["records"][0]
child=dict(process_context=dict(before=dict(page_faults=1),after=dict(page_faults=3),page_fault_delta=2),child_boundaries=s["child_boundaries"],child_gc_rows=s["child_gc_rows"],child_gc_dropped=s["child_gc_dropped"],send_ns=s["child_send_ns"],precompute_ns=s["child_precompute_ns"],construct_advance_ns=s["child_construct_ns"],shared_write=dict(begin_ns=10,end_ns=20,thread_cycles=30,payload_bytes=40),child_thread_cpu_ns=123456, sample_timings=[dict(alpha=.5,started_ns=100,completed_ns=200,wall_ns=100,thread_cycles=300,thread_cpu_ns=40,source_sample_stages=[dict(name='source_face_mask',started_ns=100,completed_ns=200,wall_ns=100,thread_cycles=300,thread_cpu_ns=40)],assembly_stages=[dict(name='sampled_roads',started_ns=100,completed_ns=200,wall_ns=100,thread_cycles=300,thread_cpu_ns=40)])])
row=dict(s,child_stages=child,parent_completed_ns=s["end_ns"])
rows=ProcessRows(2,max_record_bytes=1048576,slow_threshold_ns=1,slow_capacity=2)
rows.append(row);child["shared_write"]["payload_bytes"]=999
saved=rows.stats()["slow_process_intervals"];assert saved["dropped"]==0 and saved["records"][0]["shared_write"]["payload_bytes"]==40
record=saved['records'][0]
assert record['process_context']['before']['page_faults']==1
child['process_context']['before']['page_faults']=999
assert rows.stats()['slow_process_intervals']['records'][0]['process_context']['before']['page_faults']==1
assert record['child_thread_cpu_ns']==123456
assert record['sample_stages'][0]['thread_cpu_ns']==40
assert record['sample_stages'][0]['stages'][0]['thread_cpu_ns']==40
assert record['sample_stages'][0]['slowest_assembly_stages'][0]['thread_cpu_ns']==40
child['sample_timings'][0]['thread_cpu_ns']=999
assert rows.stats()['slow_process_intervals']['records'][0]['sample_stages'][0]['thread_cpu_ns']==40
rows.append(row);rows.append(row);assert rows.stats()["slow_process_intervals"]["dropped"]==1
out=dict(result="PASS_PRIVATE_PROCESS_CONTEXT_RETENTION",scope="Existing child/sample/source-stage/assembly CPU time copied into bounded serialized reports; mutation isolation, scalar preservation and capacity accounting. No gameplay performance claim.")
Path("outputs/nfsug-native-renderer/camera-research/process-context-retention-component-20261009.json").write_text(json.dumps(out,indent=2));print(out["result"])
