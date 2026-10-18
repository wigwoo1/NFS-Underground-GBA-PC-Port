from pathlib import Path
import json,struct,collections
from scene_batches import batches,records
p=Path('work/camera');draws=json.loads((p/'motion-draw-page-tests.json').read_text())['draws'];keys={(s['begin'],s['end']) for s in json.loads((p/'motion-model-snapshots.json').read_text())['scenes']};flips={e['frame']:e for e in records(p/'motion-original-display-world.bin') if e['pc']==0x04000000};scenes=[]
def compare(a,b):
 positions=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y];return dict(changed_bytes=len(positions),first_changed_offset=positions[0] if positions else None,last_changed_offset=positions[-1] if positions else None)
for scene in batches(p/'motion-original-source-8750-8781.bin'):
 key=(scene['begin_refresh'],scene['end_refresh'])
 if key not in keys:continue
 entries=[e for e in scene['events'] if e['pc'] in (0x030032f0,0x03000304,0x03004770)];gaps=[]
 for a,b in zip(entries,entries[1:]):
  gap=compare(Path(draws[str(a['id'])]['after_path']).read_bytes(),Path(draws[str(b['id'])]['before_path']).read_bytes());gaps.append(dict(after_event=a['id'],before_event=b['id'],**gap))
 last=Path(draws[str(entries[-1]['id'])]['after_path']).read_bytes();page=scene['display_page'];display=flips[key[1]]['blocks'][92][1];closing=compare(last[page*0xa000:page*0xa000+38400],display)
 scenes.append(dict(begin=key[0],end=key[1],source_draws=len(entries),first_draw=entries[0]['id'],last_draw=entries[-1]['id'],between_draws=gaps,last_draw_to_display=closing))
r=dict(result='AUDITED_INTERDRAW_LIFECYCLE',scenes=scenes,internal_gaps=sum(len(s['between_draws']) for s in scenes),changed_internal_gaps=sum(g['changed_bytes']>0 for s in scenes for g in s['between_draws']),closing_changed_bytes=[s['last_draw_to_display']['changed_bytes'] for s in scenes],scope='Original VRAM after draw to before next captured surface and last draw to actual displayed page. Does not identify producer routines or reconstruct scene initialization/background/HUD natively.')
(p/'motion-interdraw-lifecycle-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print({k:v for k,v in r.items() if k not in ('scenes','scope')})
