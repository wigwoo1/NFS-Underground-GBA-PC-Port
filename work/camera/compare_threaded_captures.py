"""Compare independent live captures at identical original source targets."""
import json,hashlib,sys
from pathlib import Path
from PIL import Image
sessions=[json.loads(Path(p).read_text(encoding='utf-8-sig')) for p in sys.argv[1:3]]
def load(s):
 result={}
 for f in Path(s['prefix']).parent.glob(Path(s['prefix']).name+'-capture-*-native-source.json'):
  meta=json.loads(f.read_text());base=str(f).removesuffix('-native-source.json');result[round(meta['target'],9)]=(meta,base)
 return result
left,right=map(load,sessions);matched=[]
for target in sorted(left.keys()&right.keys()):
 a,pa=left[target];b,pb=right[target];assert a==b
 packets=[Path(p+'-native-scene.bin').read_bytes() for p in (pa,pb)];assert packets[0]==packets[1]
 images=[Image.open(p+'-native.ppm') for p in (pa,pb)];assert images[0].size==images[1].size==(3840,2160);assert images[0].tobytes()==images[1].tobytes()
 matched.append(dict(target=target,alpha=a['alpha'],packet_sha256=hashlib.sha256(packets[0]).hexdigest(),exact_rgb=True))
assert matched,'No identical source targets captured; cannot infer image equivalence'
report=dict(result='PASS',matching_frames=matched,unmatched_counts=[len(left)-len(matched),len(right)-len(matched)],scope='Exact packet metadata, complete scene packet and full native 4K RGB equality at common original targets across independent runs. Unmatched captures not assessed; no temporal/scanout proof.')
Path(sessions[1]['prefix']+'-buffer-image-comparison.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
