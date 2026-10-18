"""Diagnostic complete-scene pixel-center comparison; no screen-derived geometry."""
import csv,hashlib,json,struct,sys,zlib
from pathlib import Path
source=Path(sys.argv[1]);reference_path=Path(sys.argv[2]);reference=json.loads(reference_path.read_text());assert Path(reference['input_source']).resolve()==source.resolve() and reference['original_ram_exact']
inputs=list(csv.DictReader(Path(str(source)+'-input.csv').open()));images={r['recorded_refresh']:r for r in reference['images']};checks=[]
def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
def png(width,height,rgb):
 assert len(rgb)==width*height*3
 raw=b''.join(b'\0'+rgb[y*width*3:(y+1)*width*3] for y in range(height))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
for kind in ('stable','ordered'):
 base=Path(str(source)+'-complete-'+kind);hud=Path(str(base)+'-hud.bin').read_bytes();native=Path(str(base)+'-rgb.bin').read_bytes();assert len(hud)==5591040 and len(native)==24883200
 headers=[struct.unpack_from('<IIH',hud,y*34944) for y in range(160)];refresh=headers[0][0];assert all(r==refresh and row==y and reg&7==4 for y,(r,row,reg) in enumerate(headers))
 matching=[r for r in inputs if int(r['after'])==refresh];assert len(matching)==1 and refresh in images
 item=images[refresh];assert int(matching[0]['index'])==item['index'] and int(matching[0]['keys'])==item['keys']
 raw=Path(item['png']).with_suffix('.rgba').read_bytes();assert len(raw)==153600 and hashlib.sha256(raw).hexdigest()==item['sha256'];original=b''.join(raw[i:i+3] for i in range(0,len(raw),4))
 samples=b''.join(native[((2159-int((y+.5)*13.5))*3840+300+int((x+.5)*13.5))*3:((2159-int((y+.5)*13.5))*3840+300+int((x+.5)*13.5))*3+3] for y in range(160) for x in range(240))
 differences=[max(abs(a-b) for a,b in zip(original[i:i+3],samples[i:i+3])) for i in range(0,len(original),3)]
 native_page_by_row=[(h[2]>>4)&1 for h in headers];post_original_page=(item['post_display_register']>>4)&1
 proof=None
 if kind=='stable':
  epoch,generation_a,generation_b,serial,completion,display,page=struct.unpack('<3Q4I',Path(str(base)+'-proof.bin').read_bytes());assert epoch and generation_a==generation_b and display==refresh and all(v==page for v in native_page_by_row)
  proof={'epoch':epoch,'serial':serial,'completion_refresh':completion,'display_refresh':display,'page':page,'post_original_page_matches':page==post_original_page}
 else:
  cut=struct.unpack('<I',Path(str(base)+'-cut.bin').read_bytes())[0];assert 0<=cut<=160;proof={'cut':cut,'native_page_transitions':[y for y in range(1,160) if native_page_by_row[y]!=native_page_by_row[y-1]],'post_original_page':post_original_page}
 output=Path(str(source)+'-independent-'+kind+'-comparison.png');pair=b''.join(original[y*720:(y+1)*720]+b'\xff'*36+samples[y*720:(y+1)*720] for y in range(160));output.write_bytes(png(492,160,pair));Path(str(source)+'-independent-'+kind+'-native-centers.png').write_bytes(png(240,160,samples))
 checks.append({'kind':kind,'refresh':refresh,'input_index':item['index'],'keys':item['keys'],'native_readback_sha256':hashlib.sha256(native).hexdigest(),'original_rgba_sha256':item['sha256'],'pixels':38400,'exact_rgb_pixels':differences.count(0),'pixels_max_channel_difference_le7':sum(v<=7 for v in differences),'pixels_max_channel_difference_gt32':sum(v>32 for v in differences),'mean_max_channel_difference':sum(differences)/len(differences),'proof':proof,'comparison_png':str(output)})
out={'result':'COMPLETE_SCENE_DIFFERENCES_MEASURED','source':str(source),'original_reference_report':str(reference_path),'checks':checks,'scope':'Unique original input-index/refresh joins and native proof/header validation. Original post-refresh page is not independent scanline provenance. Native 3240x2160 viewport at x=300 sampled at GBA pixel centers, GL rows flipped. Diagnostics only; no pixel-error threshold establishes fidelity, no screen-polygon matching or fractional scene interpolation comparison.'}
Path(str(source)+'-independent-scene-comparison.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
