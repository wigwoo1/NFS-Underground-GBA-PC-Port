"""Analyze actual diagnostic route timestamps without claiming gameplay cadence."""
from pathlib import Path
import json,csv,re,collections,statistics
p=Path(__file__).resolve().parent
r=json.loads((p/'threaded-racing-motion-audit.json').read_text());prefix=r['prefix']
rows=list(csv.DictReader(Path(prefix+'-worker.csv').open()));committed=[x for x in rows if x['committed']=='1']
def stats(values):
 values=sorted(values);return dict(count=len(values),median=statistics.median(values),p95=values[int((len(values)-1)*.95)],maximum=max(values))
log=Path(prefix+'-host.log').read_text();captures=re.findall(r'motion_capture_stage older=(\d+) newer=(\d+) target=([\d.]+) accepted=(\d+) stage=(\d+) cameras=(\d+) commands=(\d+) roads=(\d+)',log)
out=dict(prefix=prefix,capture_stages=dict(collections.Counter(f'accepted={x[3]},stage={x[4]}' for x in captures)),draw_ms=stats([(int(x['draw_end_ns'])-int(x['start_ns']))/1e6 for x in rows]),commit_lateness_ms=stats([(int(x['commit_begin_ns'])-int(x['deadline_ns']))/1e6 for x in committed]),commit_later_than_one_display=sum(int(x['commit_begin_ns'])-int(x['deadline_ns'])>16666667 for x in committed),committed_frames=len(committed),host_skipped=r['host_stats']['skipped'],host_unavailable=r['host_stats']['unavailable'],scope='Measured instrumented diagnostic run; commit follows deadline by design. Repeat readbacks and profiling included; no sustained60fps proof.')
(p/'racing-remaining-motion-and-pacing.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
