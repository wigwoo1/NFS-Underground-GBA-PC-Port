import json,ctypes as C
from pathlib import Path
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791505761963604700.json').read_text());rows=[x for x in r['presentation_samples'] if x['native_result']==1];gaps=[]
for a,b in zip(rows,rows[1:]):
 if (b['epoch'],b['generation'],b['display_index'])!=(a['epoch'],a['generation'],a['display_index']+1):continue
 gap=(b['callback_timing']['present_end_ns']-a['callback_timing']['present_end_ns'])/1e6
 if gap<=50:continue
 t=b['callback_timing'];prepared=b['prepared'];gaps.append(dict(index=b['display_index'],gap_ms=gap,pair_boundary=(a['source_older'],a['refresh'])!=(b['source_older'],b['refresh']),between_transactions_ms=(b['transaction_begin_ns']-a['transaction_end_ns'])/1e6,draw_ms=(t['draw_end_ns']-t['draw_begin_ns'])/1e6,present_ms=(t['present_end_ns']-t['present_begin_ns'])/1e6,source_prepare_ms=prepared['source_prepare_ns']/1e6,consumer_stages_ms={x['stage']:x['elapsed_ns']/1e6 for x in prepared['consumer_stages']},dequeue_age_ms=(b['source_dequeued_ns']-b['source_submitted_ns'])/1e6))
xinput=C.WinDLL('xinput1_4');xinput.XInputGetState.argtypes=[C.c_uint32,C.c_void_p];states=[]
for i in range(4):
 buffer=C.create_string_buffer(16);rc=xinput.XInputGetState(i,buffer);states.append(dict(slot=i,status=rc,connected=rc==0))
out=dict(result='LIVE_LONG_STALL_BREAKDOWN',gaps_over_50ms=gaps,controller_slots=states,scope='Captured CPU/API timings and current XInput connectivity. Stage wall time includes scheduling; no causal/GPU/physical-control proof.')
Path('work/camera/prototype-runs/native-depth-stalls-20261008.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
