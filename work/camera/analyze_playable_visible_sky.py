import json,struct,shutil,sys
from pathlib import Path
rp,pp,cp=map(Path,sys.argv[1:4]);cp.mkdir(exist_ok=True);(cp/'pixels').mkdir(exist_ok=True)
r=json.loads(rp.read_text());pool=json.loads(pp.read_text());records=pool['playable_sky_capture'];assert len(records)==96
samples={x['native_draw_boundary'][0]:x for x in r['presentation_samples'] if x.get('native_draw_boundary')}
checks=[];previous=None;total=0;transitions=0;boundaries=0;hudtotal=0
for index,rec in enumerate(records):
 row=rec['values'];x=samples[row[0]];assert row[1]==x['native_draw_boundary'][1] and row[4]==600+index
 assert struct.unpack('<d',struct.pack('<Q',row[2]))[0]==x['alpha']
 p=Path(rec['path']);final=p.read_bytes();sky=p.with_suffix('.sky.rgb').read_bytes();before=p.with_suffix('.prehud.rgb').read_bytes();hud=p.with_suffix('.hudmask').read_bytes();world=p.with_suffix('.worldmask').read_bytes()
 assert len(final)==len(sky)==len(before)==3240*16*3 and len(hud)==480 and len(world)==3240*16
 assert set(hud)<=set((0,1)) and set(world)<=set((0,1))
 eligible=bytearray(3240*16);count=0;moving=0
 for y in range(16):
  sy=int((648+y+.5)//13.5)-48
  for xx in range(3240):
   sx=int((xx+.5)//13.5);pixel=y*3240+xx;at=pixel*3
   if hud[sy*240+sx]:
    hudtotal+=1;assert final[at:at+3]==before[at:at+3],('HUD',index,pixel)
    if not world[pixel]:
     eligible[pixel]=1;count+=1;assert final[at:at+3]==sky[at:at+3],('sky',index,pixel)
     if previous and previous[0][pixel] and final[at:at+3]!=previous[1][at:at+3]:moving+=1
 boundary=previous is not None and (x['epoch'],x['refresh'])!=previous[2]
 total+=count;transitions+=moving>0;boundaries+=boundary and moving>0
 checks.append(dict(index=index,epoch=x['epoch'],refresh=x['refresh'],alpha=x['alpha'],visible_sky_pixels=count,moving_visible_pixels=moving,pair_boundary=boundary))
 for suffix in ('.rgb','.sky.rgb','.prehud.rgb','.hudmask','.worldmask'):shutil.copy2(p.with_suffix(suffix),cp/'pixels'/f'{index}{suffix}')
 previous=(eligible,final,(x['epoch'],x['refresh']))
assert total>0
out=dict(result='PASS_ACTUAL_PLAYABLE_VISIBLE_SKY',captures=96,visible_sky_pixel_observations=total,hud_preserved_pixel_observations=hudtotal,moving_visible_transitions=transitions,moving_visible_boundary_transitions=boundaries,checks=checks,scope='Uncovered actual world fragments plus conservative actual HUD pass-through, finalRGB exactsky, both-frame eligible motion. Bounded offscreen region only; no scanout or60fps cadence claim.')
(cp/'visible-sky-analysis.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='checks'})
