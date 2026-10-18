from pathlib import Path
import subprocess,os,sys,json
p=Path(__file__).resolve().parent;reports=[]
for enabled in [False,True]:
 env={k:v for k,v in os.environ.items() if k not in ['NF_TEST_COMPLETE_READBACK','NF_TEST_SPLIT_SCRATCH_REUSE']}
 if enabled:env['NF_TEST_SPLIT_SCRATCH_REUSE']='1'
 subprocess.run([sys.executable,str(p/'test_threaded_stable_complete.py')],env=env,check=True,stdout=subprocess.DEVNULL)
 subprocess.run([sys.executable,str(p/'profile_complete_live.py')],env=env,check=True,stdout=subprocess.DEVNULL)
 report=json.loads((p/'complete-live-profile.json').read_text());report['scratch_reuse']=enabled;reports.append(report)
(p/'split-scratch-comparison.json').write_text(json.dumps(reports,indent=2))
for report in reports:print(json.dumps(dict(reuse=report['scratch_reuse'],draw=report['draw_by_kind'],queue_full=report['host_stats']['queue_full'],skipped=report['host_stats']['skipped']),indent=2))
