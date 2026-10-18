import sys,json,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=r['world_preparation_stage_samples'];groups={}
def add(name,value):
 assert isinstance(value,(int,float)) and value>=0,(name,value)
 groups.setdefault(name,[]).append(value/1e6)
for row in rows:
 for key in ('parent_output_decode_ns','ipc_and_prepare_ns','child_prepare_ns'):add(key,row[key])
 child=row['child_stages']
 for key in ('decode_ns','history_init_ns','construct_advance_ns','precompute_ns','encode_ns','send_ns'):add('child_'+key,child[key])
 for stage in row['parent_decode_stages']:add('parent_'+stage['name'],stage['wall_ns'])
result={'result':'PASS_PROCESS_STAGE_TELEMETRY','jobs':len(rows),'stages':{},'scope':'Nested wall-time intervals overlap; do not sum them. Pipe send includes blocking, not pure serialization cost; no sole cause or cadence proof.'}
for name,values in groups.items():
 values.sort();result['stages'][name]={'count':len(values),'median_ms':statistics.median(values),'p95_ms':values[int(.95*(len(values)-1))],'max_ms':max(values)}
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
