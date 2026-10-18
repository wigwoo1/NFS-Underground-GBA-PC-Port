import argparse,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument("--executable",type=Path,required=True)
p.add_argument("--pairs",type=Path,required=True)
p.add_argument("--output",type=Path,required=True)
a=p.parse_args()
pairs=sorted(a.pairs.glob("*-old.bin"),key=lambda f:int(f.name.split("-")[0]))
assert pairs,"No captured transition pairs"
tests=[]
def replay(old,flag=None):
 command=[str(a.executable),str(old),str(old.with_name(old.name.replace("-old.bin","-new.bin")))]
 if flag:command.append(flag)
 run=subprocess.run(command,capture_output=True,text=True)
 if run.returncode:raise RuntimeError(f"{command}: {run.returncode}\n{run.stdout}\n{run.stderr}")
 row=json.loads(run.stdout.strip().splitlines()[-1]);row["pair"]=old.name;row["case"]=flag or "membership-transition";tests.append(row)
for old in pairs:replay(old)
for flag in ["--conflicting-camera","--unmatched-models","--changed-mesh"]:replay(pairs[0],flag)
report=dict(result="PASS",cases=tests,scope="Actual offscreen GPU-consumer pose assembly at alpha .25/.5/.75. Retains complete older model membership. Does not verify full-scene display pacing or game logic.")
a.output.write_text(json.dumps(report,indent=2));print("PASS",len(tests),"GPU-consumer replays",sum(r["verified_models"] for r in tests),"model pose assemblies")
