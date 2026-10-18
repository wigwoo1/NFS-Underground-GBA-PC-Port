from pathlib import Path
import subprocess,sys,os,json
p=Path(__file__).resolve().parent;reports=[];env={k:v for k,v in os.environ.items() if not k.startswith('NF_TEST_')}
for i in range(3):
 subprocess.run([sys.executable,str(p/'test_threaded_stable_complete.py')],env=env,check=True,stdout=subprocess.DEVNULL)
 subprocess.run([sys.executable,str(p/'profile_complete_live.py')],env=env,check=True,stdout=subprocess.DEVNULL)
 report=json.loads((p/'complete-live-profile.json').read_text());reports.append(report);print(json.dumps(dict(run=i,slots=report['presentation_slots'],late=report['deadline_lateness'],queue_full=report['host_stats']['queue_full'],skipped=report['host_stats']['skipped'])),flush=True)
(p/'repeated-complete-timing.json').write_text(json.dumps(dict(scope='Three four-second diagnostic held-scene runs; no smooth motion/fullroute/physical scanout proof',runs=reports),indent=2))
