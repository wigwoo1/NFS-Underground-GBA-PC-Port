from pathlib import Path
import json,struct
from scene_batches import records
p=Path('work/camera');old=list(records(p/'motion-original-sprite-inputs-world.bin'));new=list(records(p/'motion-original-video-state-world.bin'));assert len(old)==len(new)
for a,b in zip(old,new):
 for k in ('pc','frame','id','regs'):assert a[k]==b[k]
 for tag,value in a['blocks'].items():assert b['blocks'][tag]==value
scenes=[]
for e in new:
 if e['pc']!=0x04000000 or not 8757<=e['frame']<=8779:continue
 addr,data=e['blocks'][103];assert addr==0x04000000 and len(data)==96
 def half(off):return struct.unpack_from('<H',data,off)[0]
 assert half(0)==e['regs'][1]
 scenes.append(dict(refresh=e['frame'],dispcnt=hex(half(0)),bg2cnt=hex(half(12)),winin=hex(half(72)),winout=hex(half(74)),mosaic=hex(half(76)),bldcnt=hex(half(80)),bldalpha=hex(half(82)),bldy=hex(half(84)),video_io_hex=data.hex()))
assert len(scenes)==7
report=dict(result='CAPTURED_DISPLAY_VIDEO_IO',existing_records_preserved=len(old),scenes=scenes,scope='Owned shadow video IO at flip with new DISPCNT; other registers observational. No scanline history or complete native compositing proof.')
(p/'motion-video-state-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print([{k:v for k,v in s.items() if k!='video_io_hex'} for s in scenes])
