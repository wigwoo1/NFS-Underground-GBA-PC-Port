from pathlib import Path
import struct,json
p=Path('work/camera');raw=(p/'motion-live-native-model-plans.bin.wall.bin').read_bytes();offset=0;draws=[];native=[];states=[]
while offset<len(raw):
 magic,refresh,context,ok,count=struct.unpack_from('<5I',raw,offset);offset+=20
 assert magic==0x3157504e and ok and count<=120
 words=struct.unpack_from('<'+str(count*20)+'I',raw,offset);offset+=count*80
 for i in range(count):
  r=words[i*20:i*20+20];native.append([r[1],r[13],r[11],r[17],r[18],r[19]]);states.append(r)
 draws.append(dict(refresh=refresh,context=context,columns=count))
original=[];original_states=[]
raw=(p/'motion-original-scanline-state-hooks.bin').read_bytes()
for offset in range(0,len(raw),140):
 w=struct.unpack_from('<35I',raw,offset)
 if w[1]!=0x030053e8:continue
 r=w[2:18];s=w[18:];original.append([s[1],s[13],s[11],r[1],r[2],r[3]]);original_states.append(s)
compared=min(len(original),len(native))
assert native[:compared]==original[:compared],next((i for i,(a,b) in enumerate(zip(native,original)) if a!=b),None)
assert len(native)>=len(original)
start=0
for index,state in enumerate(states[:compared]):
 assert all(state[k]==original_states[start+index][k] for k in (1,2,3,4,6,7,9,11,13,16))
r=dict(result='PASS_LIVE_NATIVE_WALL_PLANS',draws=draws,columns=len(native),compared_columns=compared,pending_columns_at_capture_end=len(native)-compared,original_columns=len(original),exact_contiguous_start=start,material_and_writer_fields_exact=True,scope='Live native generation reconstructs edges from owned adjacent raw world endpoints/offsets/animation/matrix/flags before column dispatch and persistent scene submission. Original renderer runs in parallel diagnostic oracle; no GPU4K or60fps proof.')
(p/'live-native-wall-plan-tests.json').write_text(json.dumps(r,indent=2));print({k:v for k,v in r.items() if k!='draws'})
