from pathlib import Path
import subprocess,os,json,struct
p=Path('work/camera');reports=[];previous={};transitions=[]
for phase in [-.25,0,.25,.5]:
 env=os.environ.copy();env['NF_ROAD_PHASE']=str(phase);run=subprocess.run([os.sys.executable,str(p/'test_road_source_fractional_pipeline.py')],env=env,capture_output=True,text=True,timeout=180);assert run.returncode==0,(phase,run.stdout,run.stderr);report=json.loads((p/'road-source-fractional-pipeline-tests.json').read_text());assert report['phase']==phase;reports.append(report)
 for cmd in [3,4,7]:
  data=(p/f'road-{cmd}-fractional-pipeline-output.bin').read_bytes();(p/f'road-{cmd}-phase-{phase}-output.bin').write_bytes(data)
  if cmd in previous:
   pairs=list(struct.iter_unpack('<2i',data));old=list(struct.iter_unpack('<2i',previous[cmd]));transitions.append(dict(command=cmd,to_phase=phase,coverage_changes=sum(a[1]!=b[1] for a,b in zip(pairs,old)),index_changes_on_common_coverage=sum(a[1]==b[1]==1 and a[0]!=b[0] for a,b in zip(pairs,old))))
  previous[cmd]=data
result=dict(result='PASS',exact_destinations=460800,phases=reports,transitions=transitions,scope='Four translated fractional fixture phases, GPU vs independent CPU same declared integer scheduling policy. Finite phase sampling does not prove smooth native motion; coverage changes expected under integer scheduling.');(p/'road-source-fractional-phase-tests.json').write_text(json.dumps(result,indent=2));print(dict(result='PASS',exact_destinations=460800,transitions=transitions))
