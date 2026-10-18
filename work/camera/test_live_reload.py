from pathlib import Path
import csv,json,hashlib
root=Path('work/camera');baseline=list(csv.DictReader((root/'live-preview-timing.csv').open()));rows=list(csv.DictReader((root/'live-reload-timing.csv').open()))
assert len(baseline)==180 and len(rows)==360
epochs=[int(rows[0]['epoch']),int(rows[180]['epoch'])];assert epochs[1]>epochs[0]
fields=['refresh','rendered','target','older','newer','alpha']
for run in range(2):
 block=rows[run*180:(run+1)*180]
 assert all(int(row['epoch'])==epochs[run] for row in block)
 for actual,expected in zip(block,baseline):
  assert all(actual[key]==expected[key] for key in fields),(run,actual)
 assert sum(int(row['rendered']) for row in block)==171
 assert all(row['rendered']=='0' for row in block[:9])
image=(root/'live-reload-final-0.ppm').read_bytes();assert image==(root/'live-preview-final-0.ppm').read_bytes()
log=(root/'live-reload-log.txt').read_text()
for token in ['result=0','live_packets=96','rendered=342','contexts=1','uploads=73','lighting_fallbacks=0','stale_suppressed=1']:assert token in log
report={'result':'PASS','rendered_samples':342,'epochs':epochs,'both_schedules_match_reference':True,'old_epoch_submission_suppressed':True,'final_framebuffer_byte_identical':True,'framebuffer_sha256':hashlib.sha256(image).hexdigest(),'graphics_contexts':1,'unique_texture_uploads':73,'scope':'Unpaced offscreen renderer reload recovery; no visible display clearing, pacing, input latency or arbitrary camera-cut validation.'}
(root/'live-reload-tests.json').write_text(json.dumps(report,indent=2));print(report)
