"""Consume anchored plans in private replay packets; leave source fixtures intact."""
from pathlib import Path
import json,struct,os,subprocess,hashlib
from PIL import Image,ImageChops
from clip_metadata import packet_layout
from ordered_wall_plans import assemble_anchored
p=Path('work/camera').resolve()
raw=(p/'candidate-140.bin').read_bytes();h,_,ids=packet_layout(raw)
report=json.loads((p/'texture-provenance-tests.json').read_text())
dispatch=next(s for s in report['dispatch_samples'] if s['serial']==140)
commands=dispatch['commands']
sections={t:(o,n) for t,o,n in (struct.unpack_from('<3I',raw,32+i*12) for i in range(5))}
lookup={}
for i,ident in enumerate(ids):
    key=(ident[0],ident[2])
    assert key not in lookup, 'ambiguous packet surface'
    lookup[key]=i
rows=[]
for sample in report['portal_samples']:
    alpha=sample['alpha']
    if alpha==1: continue
    assembled=assemble_anchored(commands,sample['all_wall_plans'],dispatch['wall_passes'])
    assert assembled['complete']
    order=[0xffffffff if x['command'][0]==3 else lookup[(x['command'][0],x['command'][2])] for x in assembled['commands']]
    inactive=[i for i in range(len(ids)) if i not in order]
    # Packet format requires a permutation; omitted walls have empty scissors.
    assert all(ids[i][0]==2 and ids[i][2] not in {x['source'] for x in sample['all_wall_plans']} for i in inactive)
    order+=inactive
    assert sorted(i for i in order if i!=0xffffffff)==list(range(len(ids)))
    o,n=sections[3];assert n==8+len(order)*4
    patched=bytearray(raw);struct.pack_into('<'+'I'*len(order),patched,o+8,*order)
    assert patched[:o+8]==raw[:o+8] and patched[o+n:]==raw[o+n:]
    packet_layout(patched)
    label=f'ordered-all-{alpha}';packet=p/(label+'.bin');packet.write_bytes(patched)
    env=os.environ.copy();env.update(NF_CAPTURE_CLIPS=str(p/f'sampled-all-{alpha}.clips'),NF_PREVIEW_FRACTION=str(alpha),NF_PREVIEW_PHASE='2')
    subprocess.run([str(p/'sampled-clip-preview.exe'),str(packet),str(p/'order-boundary-141.bin'),str(p/label)],env=env,check=True,capture_output=True)
    with Image.open(p/(label+'-2.ppm')) as a,Image.open(p/f'sampled-all-{alpha}-2.ppm') as b:
        diff=ImageChops.difference(a,b); channels=diff.split();mask=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2]);changed=a.width*a.height-mask.histogram()[0]
    rows.append(dict(alpha=alpha,order=order,inactive=inactive,changed_pixels=changed,packet_sha256=hashlib.sha256(patched).hexdigest()))
assert all(x['changed_pixels']==0 for x in rows)
result=dict(result='PASS',samples=rows,source_sha256=hashlib.sha256(raw).hexdigest(),scope='16 offscreen 4K ordered depth replays; image equality is regression evidence, not general painter-order or 60fps gameplay proof. Inactive packet walls remain empty-clipped.')
(p/'ordered-clip-tests.json').write_text(json.dumps(result,indent=2));print('PASS',len(rows),'4K replays; images unchanged')
