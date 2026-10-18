from pathlib import Path
import struct,json
from scene_batches import records
p=Path('work/camera');raw=(p/'motion-live-native-model-plans.bin').read_bytes();off=0;plans=[];sequence=[]
while off<len(raw):
 magic,refresh,context,ok,count=struct.unpack_from('<5I',raw,off);off+=20;assert magic==0x314d504e and ok==1
 rows=[list(struct.unpack_from('<7I',raw,off+i*28)) for i in range(count)];off+=count*28
 plans.append(dict(refresh=refresh,context=context,spans=count));sequence.extend(row[1:] for row in rows)
assert off==len(raw) and len(plans)==8
original=[e for e in records(p/'motion-original-model-spans-world.bin') if e['pc']==0x03005920]
signatures=[[e['regs'][1],e['regs'][2],*struct.unpack('<5I',e['blocks'][91][1])[1:]] for e in original]
starts=[i for i in range(len(signatures)-len(sequence)+1) if signatures[i:i+len(sequence)]==sequence];assert len(starts)==1,starts
cursor=starts[0]
for plan in plans:
 matching=[e for e in records(p/'motion-original-model-rect-world.bin') if e['pc']==0x03004770 and e['frame']==plan['refresh'] and e['blocks'][51][0]==plan['context']];assert len(matching)==1
 context=matching[0]['blocks'][51][1];texture=struct.unpack_from('<I',context,52)[0];shift=struct.unpack_from('<H',context,56)[0]
 for e in original[cursor:cursor+plan['spans']]:assert e['regs'][0]==texture and struct.unpack_from('<I',e['blocks'][91][1])[0]==shift
 cursor+=plan['spans']
report=dict(result='PASS_LIVE_NATIVE_MODEL_PLANS',plans=plans,spans=len(sequence),original_spans=len(original),exact_contiguous_start=starts[0],scope='Eight actual live draw hooks generate native projection/topology/UV/row commands; exact original captured writer sequence. Read-only diagnostic hook, not live GPU adoption or fullscene60fps.')
(p/'live-native-model-plan-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)
