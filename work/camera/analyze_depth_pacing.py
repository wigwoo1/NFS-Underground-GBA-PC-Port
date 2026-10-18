from pathlib import Path
import csv,json,statistics
p=Path('work/camera/paced-depth-30s.csv');rows=list(csv.DictReader(p.open()));ready=[r for r in rows if int(r['ready'])]
ms=sorted((int(r['render_end_ns'])-int(r['render_start_ns']))/1e6 for r in ready)
report=dict(scope='30s scripted retained scene pipeline with diagnostic reversed float depth; no physical controller or perceptual gameplay validation',slots=len(rows),fresh=len(ready),repeated=sum(int(r['repeated']) for r in rows),render_ms=dict(median=statistics.median(ms),p95=ms[int(.95*(len(ms)-1))],max=max(ms)),skipped=sum(int(r['skipped']) for r in rows))
Path('work/camera/paced-depth-performance.json').write_text(json.dumps(report,indent=2));print(report)
