from pathlib import Path
import json,copy
from clip_metadata import validate
p=Path('work/camera');packet=(p/'clip-scene-141.bin').read_bytes();original=json.loads((p/'clip-scene-141.json').read_text());epoch=original['epoch'];assert validate(packet,epoch,original)
mutations=[lambda x:x.update(epoch=epoch+1),lambda x:x.update(serial=140),lambda x:x.update(begin=x['begin']+1),lambda x:x.update(end=x['end']+1),lambda x:x.update(packet_sha256='0'*64),lambda x:x['records'].pop(),lambda x:x['records'][0].update(index=999),lambda x:x['records'][0].update(ordinal=1),lambda x:x['records'][0]['identity'].__setitem__(2,0),lambda x:x['records'][0]['bounds'].__setitem__(0,-1),lambda x:x['records'][0]['bounds'].__setitem__(0,65536)]
for mutate in mutations:
 value=copy.deepcopy(original);mutate(value)
 try:validate(packet,epoch,value)
 except ValueError:pass
 else:raise AssertionError('accepted corrupt metadata')
report=dict(result='PASS',rejected_mutations=len(mutations),records=len(original['records']));(p/'clip-metadata-tests.json').write_text(json.dumps(report,indent=2));print(report)
