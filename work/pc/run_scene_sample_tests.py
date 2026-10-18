from pathlib import Path
import hashlib,json,subprocess,os
base=Path('C:/NFSUG-Workspace');old=base/'NFSUG-pc-owned-pose-timing-tests';out=base/'NFSUG-pc-scene-sample-tests';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
verified=json.loads((old/'identity-test-report.json').read_text())['test_sha256'];paths=[p for p in old.glob('owned-clock-real-*.py') if sha(p)==verified];assert len(paths)==1
text=paths[0].read_text().replace('NFSUG-pc-owned-pose-timing-tests','NFSUG-pc-scene-sample-tests').replace('timed-scenes.dll','scene-sample.dll')
marker='def check_region(old,new):';assert text.count(marker)==1;text=text.replace(marker,Path(__file__).with_name('scene_sample_checks.py').read_text()+'\n'+marker)
marker="region_counts['pairs']+=1";assert text.count(marker)==1;text=text.replace(marker,marker+';sample_check(old,new,aa,bb,pair,pi)')
text+='\nr=json.loads((out/"scene-sample-test-report.json").read_text());r["result"]="PASS_SCENE_SAMPLE_DIAGNOSTIC";r["test_sha256"]=sha(Path(__file__));(out/"scene-sample-test-report.json").write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))\n'
p=out/'scene-sample-real.py';p.write_text(text);r=subprocess.run([os.sys.executable,str(p)],capture_output=True,text=True);(out/'scene-sample-test.log').write_text(r.stdout+r.stderr);print(r.stdout[-1600:]+r.stderr,flush=True);r.check_returncode()
