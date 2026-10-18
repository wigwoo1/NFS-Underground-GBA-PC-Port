import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows={}
def walk(v):
 if isinstance(v,dict):
  d=v.get('renderer_dispatch')
  if isinstance(d,dict) and d.get('input_poll_stages') is not None:
   key=(d['thread'],d['poll_begin_ns'],d['poll_end_ns']);p=d['input_poll_stages'];assert all(isinstance(x,int) and x>=0 for x in p.values())
   assert sum(p[k] for k in ('message_pump_ns','keyboard_ns','controller_ns','snapshot_ns'))<=p['total_ns']+1 # Separate integer QPC conversions can differ by1ns.
   rows[key]=d
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
walk(r);assert rows
out={'result':'PASS_RETAINED_NATIVE_INPUT_STAGE_TRACE','qpc_partition_rounding_tolerance_ns':1,'observations':len(rows),'largest_polls':sorted(rows.values(),key=lambda x:x['input_poll_stages']['total_ns'],reverse=True),'scope':'Retained renderer dispatch observations only; not complete input-poll ledger or historic8.65s subtype proof. Native stage partition and nonnegative timing verified; no scanout/controller physical proof.'}
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],len(rows));print(out['largest_polls'][0])
