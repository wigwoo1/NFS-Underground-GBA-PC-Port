from pathlib import Path
import json,hashlib,struct
from scene_batches import records
p=Path('work/camera');old=list(records(p/'motion-original-model-spans-world.bin'));new=list(records(p/'motion-original-display-world.bin'));assert len(old)==len(new)
for a,b in zip(old,new):
 assert all(a[k]==b[k] for k in ('pc','frame','id','regs'))
 assert a['blocks']==({k:v for k,v in b['blocks'].items() if k not in (92,67)} if b['pc']==0x04000000 else b['blocks'])
keys={s['end'] for s in json.loads((p/'motion-model-snapshots.json').read_text())['scenes']};frames=[];out=p/'motion-display-assets';out.mkdir(exist_ok=True)
for e in new:
 if e['pc']!=0x04000000 or e['frame'] not in keys:continue
 address,indices=e['blocks'][92];palette=e['blocks'][67][1];assert len(indices)==38400 and len(palette)==512
 page=1 if e['regs'][1]&16 else 0;assert address==0x06000000+page*0xa000
 prefix=out/str(e['frame']);Path(str(prefix)+'-indices.bin').write_bytes(indices);Path(str(prefix)+'-palette.bin').write_bytes(palette)
 colors=[struct.unpack_from('<H',palette,i*2)[0] for i in range(256)];rgb=bytes(channel for i in indices for channel in ((colors[i]&31)*255//31,((colors[i]>>5)&31)*255//31,((colors[i]>>10)&31)*255//31));Path(str(prefix)+'.ppm').write_bytes(b'P6\n240 160\n255\n'+rgb)
 frames.append(dict(refresh=e['frame'],page=page,indices_sha256=hashlib.sha256(indices).hexdigest(),palette_sha256=hashlib.sha256(palette).hexdigest(),indices_path=str(prefix)+'-indices.bin',palette_path=str(prefix)+'-palette.bin',original_rgb_preview=str(prefix)+'.ppm'))
assert len(frames)==7
last=frames[-1];actual=Path(last['indices_path']).read_bytes();native=(p/'native-all-surface-buffer.bin').read_bytes()[last['page']*0xa000:last['page']*0xa000+38400];difference=sum(a!=b for a,b in zip(actual,native))
r=dict(result='CAPTURED_ACTUAL_DISPLAY_PAGES',existing_events_exact=len(old),frames=frames,final_display_difference_from_uncleared_surface_composition=difference,scope='Exact page and palette at original DISPCNT flip; existing trace and finalRAM unchanged. RGB previews are original240x160 display diagnostics. Surface composition omits clears/background/HUD and is not claimed display-identical or native4K.')
(p/'motion-display-tests.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(r['result'],len(frames),len(old),difference)
