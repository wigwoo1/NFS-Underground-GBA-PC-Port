"""Real source identity/time joins and malformed ownership rejection."""
import json, struct
from pathlib import Path
from owned_model_builder_inputs import OwnedModelBuilders
report=json.loads(Path('work/camera/prototype-runs/owned-native-1791279461173682600.json').read_text())
p=Path(report['model_pose_trace']); raw=p.with_suffix('.builders.bin').read_bytes()
store=OwnedModelBuilders(raw); checks=0
poses=p.read_bytes()
for at in range(0,len(poses),292):
    h=struct.unpack_from('<8I',poses,at)
    model=struct.unpack_from('<h',poses,at+32+54)[0]
    if 31<=model<=36:
        value=store.at(h[3],h[5],h[1])
        assert value.refresh<=h[1] and value.object_address==h[3] and value.matrix_address==h[5]
        checks+=1
assert checks==291
for invalid in (raw[:-1], b'\0'*292):
    try: OwnedModelBuilders(invalid)
    except ValueError: pass
    else: raise AssertionError('Malformed builder accepted')
first=raw[:292]; header=list(struct.unpack_from('<8I',first)); header[1]+=1
newer=struct.pack('<8I',*header)+first[32:]
try: OwnedModelBuilders(newer+first)
except ValueError: pass
else: raise AssertionError('Refresh reset accepted')
for key, values in store.records.items():
    try: store.at(*key, values[0].refresh-1)
    except ValueError: pass
    else: raise AssertionError('Future builder accepted')
    break
try: store.at(0,0,0)
except ValueError: pass
else: raise AssertionError('Missing identity accepted')
changed=bytearray(first); changed[32]^=1
same=OwnedModelBuilders(first+bytes(changed)); h=struct.unpack_from('<8I',first)
assert same.at(h[3],h[4],h[1]).source==bytes(changed[32:196])
print('PASS: 291 immutable source/time joins, malformed/reset/future/missing rejection, same-refresh ordering')
