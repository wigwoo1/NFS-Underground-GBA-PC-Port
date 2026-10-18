"""Derive bounded GPU fixtures from original events through the last selected owner."""
import hashlib,json,shutil,struct
from pathlib import Path
import argparse
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=Path('C:/NFSUG-Workspace/NFSUG-restored-composition-fixtures'));p.add_argument('--output',type=Path,default=Path('C:/NFSUG-Workspace/NFSUG-restored-composition-gpu-fixtures'));args=p.parse_args();source=args.source;out=args.output;out.mkdir(exist_ok=True);capture=json.loads((source/'source-fixture-capture-report.json').read_text())
maximum=max(r['owner']['end'] for r in capture['road_records']);at=0;end=0;events=0;previous=0;ordinal=0
with (source/'original-road-events.nrj').open('rb') as stream:
 while header:=stream.read(96):
  assert len(header)==96;h=struct.unpack('<12Q',header);assert h[0]==0x314a524e and h[1]==1 and h[2]==96+h[7]*68+h[10] and h[5]>=previous and h[4]>ordinal
  stream.seek(h[2]-96,1);at=stream.tell();previous=h[5];ordinal=h[4]
  if h[5]<=maximum:end=at;events+=1
assert 96<=end<=64*1024*1024
with (source/'original-road-events.nrj').open('rb') as stream:(out/'original-road-events.nrj').write_bytes(stream.read(end))
names={'source-fixture-capture-report.json','road-candidates.bin'}
for entry in capture['fixtures'].values():names.add(entry['filename']);names.add(f"retention-{entry['refresh']}.ref")
for record in capture['road_records']:
 names.update((record['provenance']['filename'],record['full_replay']['filename'],f"owner-{record['owner']['serial']}.nrp"));names.update(a['filename'] for a in record['assets'])
for name in sorted(names):
 assert Path(name).name==name;shutil.copyfile(source/name,out/name)
report=dict(result='PASS_BOUNDED_ORIGINAL_ROAD_PREFIX',maximum_owner_end=maximum,original_full_journal_bytes=(source/'original-road-events.nrj').stat().st_size,selected_prefix_bytes=end,selected_prefix_events=events,selected_prefix_sha256=hashlib.sha256((out/'original-road-events.nrj').read_bytes()).hexdigest(),snapshots=len(capture['fixtures']),source_journal_preserved=True,selection='All original road events through latest selected source owner; no GPU hole or screen matching')
(out/'prefix-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
