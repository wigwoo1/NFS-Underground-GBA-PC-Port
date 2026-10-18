"""Independent BGR555 historical-palette oracle for captured source backgrounds."""
from pathlib import Path
import hashlib,json,struct
import argparse
p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,default=Path('C:/NFSUG-Workspace/NFSUG-restored-composition-gpu-fixtures'));folder=p.parse_args().folder;capture=json.loads((folder/'source-fixture-capture-report.json').read_text());records=[]
for entry in capture['fixtures'].values():
 raw=(folder/entry['filename']).read_bytes();h=struct.unpack_from('<16Q',raw);sky=raw[h[8]:h[8]+h[9]];sh=struct.unpack_from('<16Q',sky);nab=sky[sh[8]:sh[8]+sh[9]];nh=struct.unpack_from('<16Q',nab);layer=nab[nh[12]:nh[12]+nh[13]];rgba=bytearray(153600)
 for y in range(160):
  owner=int(h[5]==2 and y>=h[6]);bg=raw[h[10+owner*2]:h[10+owner*2]+76880];ref=struct.unpack_from('<H',layer,20512+(y*25+24)*2)[0]
  for x in range(240):
   cell=y*240+x
   if bg[38480+cell]:
    color=struct.unpack_from('<H',layer,28512+ref*4096+bg[80+cell]*2)[0]
    for c in range(3):v=(color>>(c*5))&31;rgba[cell*4+c]=(v<<3)|(v>>2)
    rgba[cell*4+3]=255
 name=f"background-{entry['refresh']}.rgba";(folder/name).write_bytes(rgba);records.append(dict(file=name,sha256=hashlib.sha256(rgba).hexdigest()))
(folder/'background-reference-report.json').write_text(json.dumps(dict(result='PASS_PREPARED_ORIGINAL_BACKGROUND_PALETTE_REFERENCES',references=records),indent=2));print('Prepared independent background references',len(records))
