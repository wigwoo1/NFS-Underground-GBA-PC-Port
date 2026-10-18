from pathlib import Path
import csv,struct,json
p=Path(__file__).resolve().parent/'prototype-runs';done=max(p.glob('*-bitmap-blits.csv.glyphs-done.csv'),key=lambda p:p.stat().st_mtime);rows=list(csv.DictReader(done.open()));raw=done.with_name(done.name.removesuffix('.glyphs-done.csv')+'.glyphs.bin').read_bytes();off=0;calls=0;pixels=0
while off<len(raw):
 h=struct.unpack_from('<16I',raw,off);off+=64;frame,pc,descriptor,glyph,dest,stride,pal,w,height,dw,flags,transparent,source,size,lr,target=h;off+=size;r=rows[calls];selected=(int(r['entry_display'],16)>>4)&1;page=int(dest>=0x0600a000);base=0x06000000+page*0xa000;assert page!=selected and ((int(r['exit_display'],16)>>4)&1)==selected
 assert base<=dest and dest+(height-1)*stride+dw<=base+38400;pixels+=height*dw;calls+=1
report={'result':'PASS','hidden_page_complete_footprints':calls,'tested_destination_pixels':pixels,'cross_refresh_calls':sum(r['begin']!=r['end'] for r in rows),'scope':'985 observed complete glyph footprints hidden through actual return; futureflip/clear ownership remains unverified'};done.with_suffix('.page-verification.json').write_text(json.dumps(report,indent=2));print(report)
