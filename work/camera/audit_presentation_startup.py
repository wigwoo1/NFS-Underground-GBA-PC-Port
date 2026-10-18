"""Audit startup availability and original-clock presentation ownership."""
from pathlib import Path
import csv,json,math,sys
p=Path('work/camera');source=p/(sys.argv[1] if len(sys.argv)>1 else 'live-world-classified-fullroute.csv');rows=list(csv.DictReader(source.open()));assert rows
rate=16777216/280896;first=rows[0];start=int(first['refresh'])-int(first['simulated']);delay=start-float(first['target']);first_ready=next(i for i,r in enumerate(rows) if int(r['ready']));post=rows[first_ready:]
max_target_error=max_alpha_error=0
phase_logged=all(k in first for k in ("source_older_refresh","source_newer_refresh"))
for i,r in enumerate(rows):
 display=int(r['display_index']);simulated=int(r['simulated']);refresh=int(r['refresh']);target=float(r['target'])
 assert refresh==start+simulated,(i,'simulation refresh ownership')
 error=abs(target-(start+display*rate/60-delay));max_target_error=max(max_target_error,error);assert error<1e-8,(i,'original clock target',error)
 if i:assert display-int(rows[i-1]['display_index'])==1+int(r['skipped']),(i,'unaccounted display deadline')
 if int(r['ready']):
  older=int(r['older']);newer=int(r['newer']);alpha=float(r['alpha']);assert older<=newer and 0<=alpha<=1
  if i and int(rows[i-1]['ready']) and (older,newer)==(int(rows[i-1]['older']),int(rows[i-1]['newer'])):assert alpha>=float(rows[i-1]['alpha']),(i,'same-pair phase reversed')
  if phase_logged:
   left=int(r['source_older_refresh']);right=int(r['source_newer_refresh']);assert left<=target<=right
   expected=(target-left)/(right-left) if right!=left else 0
   error=abs(alpha-expected);max_alpha_error=max(max_alpha_error,error);assert error<1e-8,(i,'original pair alpha',error)
  assert not int(r['epoch_mismatch'])
startup=rows[:first_ready];assert all(not int(r['ready']) for r in startup)
report=dict(result='PASS',source=source.name,display_samples=len(rows),starting_refresh=start,presentation_delay_refreshes=delay,original_game_refresh_hz=rate,first_ready_display=int(post[0]['display_index']),startup_unavailable_samples=len(startup),startup_empty=sum(int(r['timeline_status'])==0 for r in startup),startup_before_first_scene=sum(int(r['timeline_status'])==1 for r in startup),first_ready_deadline_ms=int(post[0]['deadline_ns'])/1e6,post_startup_unavailable=sum(not int(r['ready']) for r in post),post_startup_repeated=sum(int(r['repeated']) for r in post),skipped_deadlines=sum(int(r['skipped']) for r in rows),max_original_clock_target_error=max_target_error,same_pair_phase_monotonic=True,pair_phase_formula_verified=phase_logged,max_pair_alpha_error=max_alpha_error,scope='Recorded simulation clock, scene handles/phase range and startup availability only; scene timestamps are not logged, so pair alpha formula is not independently verified; no full-scene pixel motion or physical scanout proof.')
assert report['post_startup_unavailable']==0 and report['post_startup_repeated']==0
if phase_logged:report['scope']='Recorded original simulation clock and acquired scene timestamp/alpha formula verification; no full-scene pixel motion or physical scanout proof.'
(p/'presentation-startup-clock-audit.json').write_text(json.dumps(report,indent=2));print(report)
