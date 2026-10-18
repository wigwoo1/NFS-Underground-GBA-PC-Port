from pathlib import Path
import json,struct
p=Path('work/camera');raw=(p/'motion-live-native-model-plans.bin.road.bin').read_bytes();offset=0;draws=[];commands=[]
while offset<len(raw):
 magic,refresh,context,ok,count,lo,hi=struct.unpack_from('<7I',raw,offset);offset+=28
 assert magic==0x3152504e and ok and count<=8192
 words=struct.unpack_from('<'+str(count*17)+'I',raw,offset);offset+=count*68
 missing=lo|(hi<<32)
 if len(draws)>=2:
  assert not missing
  commands.extend([list(words[i*17:i*17+17]) for i in range(count)])
 draws.append(dict(refresh=refresh,runs=count,missing_depth_mask=missing))
reference=json.loads((p/'native-road-writer-calls.json').read_text())
assert commands==[[*c['params'],c['signature'][-1]] for c in reference]
r=dict(result='PASS_LIVE_NATIVE_RAW_ROAD_PLANS',draws=draws,post_warmup_runs=len(commands),exact_reference_commands=True,scope='Native commands generated in live read-only hook from owned raw source blocks. Two initial warmup draws excluded; original renderer remains active.')
(p/'live-native-road-plan-tests.json').write_text(json.dumps(r,indent=2));print({k:v for k,v in r.items() if k!='draws'})
