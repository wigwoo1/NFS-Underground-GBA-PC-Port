from pathlib import Path
import json,struct
from scene_batches import records
p=Path('work/camera');calls=json.loads((p/'native-model-writer-calls.json').read_text());snap={m['event']:m for s in json.loads((p/'motion-model-snapshots.json').read_text())['scenes'] for m in s['models']};original=[e for e in records(p/'motion-original-model-spans-world.bin') if e['pc']==0x03005920]
signatures=[]
for e in original:
 shift,U,V,du,dv=struct.unpack('<5I',e['blocks'][91][1]);signatures.append([e['regs'][1],e['regs'][2],U,V,du,dv])
native=[c['params'] for c in calls];starts=[i for i in range(len(original)-len(native)+1) if signatures[i:i+len(native)]==native];assert len(starts)==1,starts
for i,c in enumerate(calls):
 e=original[starts[0]+i];m=snap[c['event']];shift=struct.unpack('<5I',e['blocks'][91][1])[0];texture=struct.unpack_from('<I',bytes.fromhex(m['context_hex']),52)[0];assert e['regs'][0]==texture and shift==m['width'].bit_length()-1
 c['texture']=texture;c['shift']=shift;c['oracle_regs']=list(e['regs'][:3]);c['oracle_globals']=list(struct.unpack('<5I',e['blocks'][91][1]))
r=dict(result='PASS_ACTUAL_NATIVE_MODEL_SEQUENCE',native_spans=len(calls),captured_spans=len(original),exact_contiguous_start=starts[0],native_texture_shape_fields_exact=len(calls),scope='Native world model projection/source-topology/edge-walk row parameters form one exact contiguous actual captured writer sequence with matching texture/shift. Capture prefix/suffix excluded; palette/display/fullscene timing unverified.')
(p/'native-model-captured-sequence-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');(p/'native-model-joined-writer-calls.json').write_text(json.dumps(calls,indent=2),encoding='utf-8');print(r)
