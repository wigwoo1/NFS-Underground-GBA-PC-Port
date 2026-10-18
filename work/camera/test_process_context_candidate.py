from owned_process_context_candidate import read,C,Counters
import json
from pathlib import Path
assert C.sizeof(Counters)==72
before=read()
memory=bytearray(8*1024*1024)
for offset in range(0,len(memory),4096):memory[offset]=1
after=read()
assert before["priority_class"]==after["priority_class"] and before["working_set_bytes"]>0 and after["private_commit_bytes"]>0
out=dict(result="PASS_SELF_PROCESS_CONTEXT",before=before,after=after,page_fault_delta=(after["page_faults"]-before["page_faults"])&0xffffffff,scope="Read-only self process metrics, allocation touch. Faults include soft faults and do not prove disk paging.")
Path("outputs/nfsug-native-renderer/camera-research/process-context-component-20261009.json").write_text(json.dumps(out,indent=2));print(out)
