from pathlib import Path
import json,struct,os
from scene_batches import batches
from draw_order import draw_order
root=Path('work/camera');scenes=list(batches(root/'world.bin'));scene=scenes[int(os.environ.get('NF_REPLAY_SCENE','10'))];order,counts=draw_order(scene)
assert counts['model']==1,'This replay supports one model only'
commands=[0xffffffff if x['kind']=='model' else x['index']+(counts['road'] if x['kind']=='wall' else 0) for x in order]
assert sorted(v for v in commands if v!=0xffffffff)==list(range(counts['road']+counts['wall']))
(root/'draw-order.bin').write_bytes(struct.pack('<2I',0x314f464e,len(commands))+struct.pack('<'+'I'*len(commands),*commands))
report={'scene_serial':scene['serial'],'counts':counts,'commands':order,'scope':'Captured high-level order only; intra-wall shading passes and visibility between simulation updates are not covered.'}
(root/'draw-order.json').write_text(json.dumps(report,indent=2));print(counts, [x['kind'] for x in order])
